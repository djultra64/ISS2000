// Original project work: djultra64. ZIP decoding uses the upstream miniz library.
#include "rom_image.hpp"
#include "game_revision.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cerrno>
#include <fstream>
#include <limits>
#include <random>
#include <stdexcept>
#include <system_error>

#include "miniz.h"

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#include <sys/file.h>
#include <sys/stat.h>
#endif

namespace iss2000 {
namespace {
constexpr std::size_t rom_size = 16U * 1024U * 1024U;
constexpr std::size_t max_archive_size = 64U * 1024U * 1024U;
constexpr auto expected_sha256 = active_revision().sha256;

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

std::uint32_t magic(std::span<const std::uint8_t> bytes) {
    if (bytes.size() < 4) return 0;
    return (std::uint32_t(bytes[0]) << 24) | (std::uint32_t(bytes[1]) << 16) |
           (std::uint32_t(bytes[2]) << 8) | bytes[3];
}

bool is_raw_magic(std::uint32_t value) {
    return value == 0x80371240U || value == 0x37804012U || value == 0x40123780U;
}

void validate_canonical(std::span<const std::uint8_t> bytes) {
    if (bytes.size() != rom_size) fail("Unsupported ROM size: expected exactly 16 MiB");
    if (magic(bytes) != 0x80371240U) fail("Expected canonical big-endian N64 ROM bytes");
    if (rom_detail::sha256_hex(bytes) != expected_sha256)
        fail(std::string("Unsupported or corrupted ISS2000 ROM: SHA-256 does not match ")+active_revision().description);
}

struct ZipReader {
    mz_zip_archive archive{};
    bool initialized = false;
    ~ZipReader() { if (initialized) mz_zip_reader_end(&archive); }
};

std::vector<std::uint8_t> read_zip(std::span<const std::uint8_t> bytes) {
    ZipReader reader;
    reader.initialized = mz_zip_reader_init_mem(&reader.archive, bytes.data(), bytes.size(), 0) != 0;
    if (!reader.initialized) fail("Cannot read input: unrecognized ROM or invalid ZIP archive");
    mz_uint selected = 0;
    unsigned candidates = 0;
    mz_zip_archive_file_stat selected_stat{};
    const mz_uint count = mz_zip_reader_get_num_files(&reader.archive);
    for (mz_uint index = 0; index < count; ++index) {
        mz_zip_archive_file_stat stat{};
        if (!mz_zip_reader_file_stat(&reader.archive, index, &stat))
            fail("Cannot read ZIP member metadata");
        if (stat.m_is_directory) continue;
        const mz_uint name_size = mz_zip_reader_get_filename(&reader.archive, index, nullptr, 0);
        if (!name_size) fail("Cannot read ZIP member name");
        std::string name(name_size, '\0');
        if (mz_zip_reader_get_filename(&reader.archive, index, name.data(), name_size) != name_size)
            fail("Cannot read complete ZIP member name");
        name.resize(name_size-1);
        auto dot = name.find_last_of('.');
        if (dot == std::string::npos) continue;
        std::string suffix = name.substr(dot);
        for (char& ch : suffix) if (ch >= 'A' && ch <= 'Z') ch += 'a'-'A';
        if (suffix != ".z64" && suffix != ".n64" && suffix != ".v64") continue;
        ++candidates;
        selected = index;
        selected_stat = stat;
    }
    if (candidates != 1) fail("ZIP archive must contain exactly one ROM member");
    // Bound allocation and reject a claimed-size bomb before decompression.
    if (selected_stat.m_uncomp_size != rom_size)
        fail("ZIP member has unsupported decompressed size: expected exactly 16 MiB");
    if (selected_stat.m_is_encrypted || !selected_stat.m_is_supported)
        fail("ZIP ROM member is encrypted or uses unsupported compression");
    std::vector<std::uint8_t> result(rom_size);
    if (!mz_zip_reader_extract_to_mem(&reader.archive, selected, result.data(), result.size(), 0))
        fail("Cannot extract ZIP ROM member: corrupt data or CRC mismatch");
    return result;
}

void check_destination(const std::filesystem::path& destination, bool require_missing=true) {
    for (auto path = destination; !path.empty();) {
        std::error_code error;
        const auto status = std::filesystem::symlink_status(path, error);
        if (error && error != std::errc::no_such_file_or_directory)
            throw std::system_error(error, "Cannot inspect ROM destination");
        if (std::filesystem::is_symlink(status)) fail("ROM output paths must not contain symlinks");
        if (require_missing && path == destination && status.type() != std::filesystem::file_type::not_found)
            fail("ROM destination already exists; refusing to overwrite it");
        auto parent = path.parent_path();
        if (parent == path) break;
        path = std::move(parent);
    }
}

// Persistent lock inode avoids stale lock directories after a process crash.
// Every recovery for this destination uses the same OS-managed advisory lock.
class StorageLock {
public:
    explicit StorageLock(std::filesystem::path path) {
        path += ".import-lock";
#ifdef _WIN32
        file_=CreateFileW(path.c_str(),GENERIC_READ|GENERIC_WRITE,
                          FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,
                          FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,nullptr);
        if (file_==INVALID_HANDLE_VALUE)
            throw std::system_error(GetLastError(),std::system_category(),"Cannot lock ROM storage");
        BY_HANDLE_FILE_INFORMATION info{};
        if (!GetFileInformationByHandle(file_,&info) ||
                (info.dwFileAttributes & (FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY))) {
            CloseHandle(file_); file_=INVALID_HANDLE_VALUE;
            fail("ROM storage lock must be a regular file");
        }
        if (!LockFileEx(file_,LOCKFILE_EXCLUSIVE_LOCK,0,MAXDWORD,MAXDWORD,&overlap_)) {
            auto error=GetLastError(); CloseHandle(file_); file_=INVALID_HANDLE_VALUE;
            throw std::system_error(error,std::system_category(),"Cannot acquire ROM storage lock");
        }
#else
        file_=::open(path.c_str(),O_RDWR|O_CREAT|O_NOFOLLOW,0600);
        if (file_<0) throw std::system_error(errno,std::generic_category(),"Cannot lock ROM storage");
        struct stat info{};
        if (::fstat(file_,&info)<0 || !S_ISREG(info.st_mode)) {
            ::close(file_); file_=-1; fail("ROM storage lock must be a regular file");
        }
        while (::flock(file_,LOCK_EX)<0) {
            if (errno==EINTR) continue;
            const auto error=errno; ::close(file_); file_=-1;
            throw std::system_error(error,std::generic_category(),"Cannot acquire ROM storage lock");
        }
#endif
    }
    StorageLock(const StorageLock&)=delete;
    StorageLock& operator=(const StorageLock&)=delete;
    ~StorageLock() {
#ifdef _WIN32
        if (file_!=INVALID_HANDLE_VALUE) {
            UnlockFileEx(file_,0,MAXDWORD,MAXDWORD,&overlap_); CloseHandle(file_);
        }
#else
        if (file_>=0) { ::flock(file_,LOCK_UN); ::close(file_); }
#endif
    }
private:
#ifdef _WIN32
    HANDLE file_=INVALID_HANDLE_VALUE;
    OVERLAPPED overlap_{};
#else
    int file_=-1;
#endif
};

bool same_bytes(const std::filesystem::path& path,std::span<const std::uint8_t> bytes) {
    std::error_code error;
    if (std::filesystem::file_size(path,error)!=bytes.size() || error) return false;
    std::ifstream input(path,std::ios::binary);
    if (!input) return false;
    std::array<std::uint8_t,65536> buffer{};
    for (std::size_t offset=0; offset<bytes.size();) {
        const auto size=std::min(buffer.size(),bytes.size()-offset);
        if (!input.read(reinterpret_cast<char*>(buffer.data()),size)) return false;
        if (!std::equal(buffer.begin(),buffer.begin()+size,bytes.begin()+offset)) return false;
        offset+=size;
    }
    return input.peek()==std::char_traits<char>::eof();
}

std::filesystem::path preserve_invalid(const std::filesystem::path& source) {
    for (std::uint64_t number=0;;++number) {
        auto backup=source;
        backup += number ? "."+std::to_string(number)+".invalid-backup" : ".invalid-backup";
#ifdef _WIN32
        // MoveFileEx without REPLACE_EXISTING never removes a prior backup.
        std::error_code status_error;
        if (std::filesystem::symlink_status(backup,status_error).type()!=std::filesystem::file_type::not_found &&
                !status_error) continue;
        if (MoveFileExW(source.c_str(),backup.c_str(),MOVEFILE_WRITE_THROUGH)) return backup;
        const auto error=GetLastError();
        if (error==ERROR_ALREADY_EXISTS || error==ERROR_FILE_EXISTS) continue;
        throw std::system_error(error,std::system_category(),"Cannot preserve previous ROM storage");
#else
        // link() is exclusive even if another process creates this backup name
        // after inspection. The old inode is preserved before its name moves.
        std::error_code error;
        std::filesystem::create_hard_link(source,backup,error);
        if (error==std::errc::file_exists) continue;
        if (error) throw std::system_error(error,"Cannot preserve previous ROM storage");
        if (!std::filesystem::remove(source,error) || error)
            fail("Previous ROM backup is preserved, but original storage could not be released");
        return backup;
#endif
    }
}

std::filesystem::path temporary_path(const std::filesystem::path& parent) {
    static std::atomic<std::uint64_t> sequence{0};
    std::random_device random;
    return parent / (".iss2000-import-" + std::to_string(random()) + "-" +
                     std::to_string(random()) + "-" + std::to_string(sequence++) + ".tmp");
}

// Fixed SHA-256 round constants and initial values follow the published
// algorithm. The implementation below is original project code.
constexpr std::array<std::uint32_t,64> sha_constants{
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};

void sha_block(std::array<std::uint32_t,8>& state, const std::uint8_t* bytes) {
    std::array<std::uint32_t,64> words{};
    for (unsigned i=0; i<16; ++i)
        words[i] = (std::uint32_t(bytes[4*i])<<24) | (std::uint32_t(bytes[4*i+1])<<16) |
                   (std::uint32_t(bytes[4*i+2])<<8) | bytes[4*i+3];
    for (unsigned i=16; i<64; ++i) {
        const auto a = words[i-15], b = words[i-2];
        const auto s0 = std::rotr(a,7) ^ std::rotr(a,18) ^ (a>>3);
        const auto s1 = std::rotr(b,17) ^ std::rotr(b,19) ^ (b>>10);
        words[i] = words[i-16] + s0 + words[i-7] + s1;
    }
    auto [a,b,c,d,e,f,g,h] = state;
    for (unsigned i=0; i<64; ++i) {
        const auto s1 = std::rotr(e,6) ^ std::rotr(e,11) ^ std::rotr(e,25);
        const auto choose = (e&f) ^ (~e&g);
        const auto t1 = h+s1+choose+sha_constants[i]+words[i];
        const auto s0 = std::rotr(a,2) ^ std::rotr(a,13) ^ std::rotr(a,22);
        const auto majority = (a&b) ^ (a&c) ^ (b&c);
        const auto t2 = s0+majority;
        h=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
    }
    const std::array<std::uint32_t,8> next{a,b,c,d,e,f,g,h};
    for (unsigned i=0; i<8; ++i) state[i] += next[i];
}
}

namespace rom_detail {
std::vector<std::uint8_t> normalize_byte_order(std::span<const std::uint8_t> bytes) {
    if (bytes.size() < 4 || bytes.size()%4) fail("ROM is truncated or not word-aligned");
    const auto order = magic(bytes);
    if (!is_raw_magic(order)) fail("Unrecognized N64 ROM byte-order magic");
    std::vector<std::uint8_t> result(bytes.begin(),bytes.end());
    if (order == 0x37804012U)
        for (std::size_t i=0; i<result.size(); i+=2) std::swap(result[i],result[i+1]);
    else if (order == 0x40123780U)
        for (std::size_t i=0; i<result.size(); i+=4) {
            std::swap(result[i],result[i+3]); std::swap(result[i+1],result[i+2]);
        }
    return result;
}

std::string sha256_hex(std::span<const std::uint8_t> bytes) {
    std::array<std::uint32_t,8> state{0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                                      0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    std::size_t consumed=0;
    for (; bytes.size()-consumed>=64; consumed+=64) sha_block(state,bytes.data()+consumed);
    std::array<std::uint8_t,128> tail{};
    const auto remaining=bytes.size()-consumed;
    std::copy_n(bytes.begin()+consumed,remaining,tail.begin());
    tail[remaining]=0x80;
    const std::size_t padded=remaining<56 ? 64 : 128;
    const auto bits=std::uint64_t(bytes.size())*8U;
    for (unsigned i=0; i<8; ++i) tail[padded-1-i] = static_cast<std::uint8_t>(bits>>(8*i));
    sha_block(state,tail.data());
    if (padded==128) sha_block(state,tail.data()+64);
    constexpr char digits[]="0123456789abcdef";
    std::string result;
    result.reserve(64);
    for (auto word : state)
        for (int shift=28; shift>=0; shift-=4) result.push_back(digits[(word>>shift)&15]);
    return result;
}

void write_bytes_exclusive(const std::filesystem::path& target,
                           std::span<const std::uint8_t> bytes) {
    if (target.empty() || target.filename().empty()) fail("ROM destination must name a file");
    const auto destination=std::filesystem::absolute(target).lexically_normal();
    check_destination(destination);
    std::filesystem::create_directories(destination.parent_path());
    const auto temporary=temporary_path(destination.parent_path());
    bool created=false;
    try {
#ifdef _WIN32
        HANDLE file=CreateFileW(temporary.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,
                                FILE_ATTRIBUTE_NORMAL,nullptr);
        if (file==INVALID_HANDLE_VALUE)
            throw std::system_error(GetLastError(),std::system_category(),"Cannot create temporary ROM file");
        created=true;
        try {
            std::size_t offset=0;
            while (offset<bytes.size()) {
                DWORD written=0;
                const auto count=static_cast<DWORD>(std::min<std::size_t>(bytes.size()-offset,1U<<20));
                if (!WriteFile(file,bytes.data()+offset,count,&written,nullptr) || !written)
                    throw std::system_error(GetLastError(),std::system_category(),"Cannot write ROM file");
                offset+=written;
            }
            if (!FlushFileBuffers(file))
                throw std::system_error(GetLastError(),std::system_category(),"Cannot flush ROM file");
        } catch (...) { CloseHandle(file); throw; }
        if (!CloseHandle(file))
            throw std::system_error(GetLastError(),std::system_category(),"Cannot close ROM file");
        // No MOVEFILE_REPLACE_EXISTING: an existing destination always wins.
        if (!MoveFileExW(temporary.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH))
            throw std::system_error(GetLastError(),std::system_category(),"Cannot publish ROM without overwriting");
        created=false;
#else
        const int file=::open(temporary.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW,0600);
        if (file<0) throw std::system_error(errno,std::generic_category(),"Cannot create temporary ROM file");
        created=true;
        try {
            std::size_t offset=0;
            while (offset<bytes.size()) {
                const auto written=::write(file,bytes.data()+offset,std::min<std::size_t>(bytes.size()-offset,1U<<20));
                if (written<0 && errno==EINTR) continue;
                if (written<=0) throw std::system_error(errno,std::generic_category(),"Cannot write ROM file");
                offset+=static_cast<std::size_t>(written);
            }
            if (::fsync(file)<0) throw std::system_error(errno,std::generic_category(),"Cannot flush ROM file");
        } catch (...) { ::close(file); throw; }
        if (::close(file)<0) throw std::system_error(errno,std::generic_category(),"Cannot close ROM file");
        // A same-directory hard link publishes the complete inode atomically;
        // link() fails for any existing entry, including dangling symlinks.
        std::filesystem::create_hard_link(temporary,destination);
        std::filesystem::remove(temporary);
        created=false;
#endif
    } catch (...) {
        if (created) { std::error_code ignored; std::filesystem::remove(temporary,ignored); }
        throw;
    }
}

void ensure_bytes_storage(const std::filesystem::path& target,
                          std::span<const std::uint8_t> bytes) {
    if (target.empty() || target.filename().empty()) fail("ROM destination must name a file");
    const auto destination=std::filesystem::absolute(target).lexically_normal();
    check_destination(destination,false);
    if (same_bytes(destination,bytes)) return;
    std::filesystem::create_directories(destination.parent_path());
    StorageLock lock(destination);
    check_destination(destination,false);
    // Another process may have installed the same complete image while this
    // process waited for the lock; it is then a no-op, without extra backups.
    if (same_bytes(destination,bytes)) return;
    std::error_code error;
    const auto status=std::filesystem::symlink_status(destination,error);
    if (error && error!=std::errc::no_such_file_or_directory)
        throw std::system_error(error,"Cannot inspect existing ROM storage");
    bool preserved=false;
    if (status.type()!=std::filesystem::file_type::not_found) {
        if (!std::filesystem::is_regular_file(status)) fail("ROM storage must be a regular file");
        preserve_invalid(destination);
        preserved=true;
    }
    try { write_bytes_exclusive(destination,bytes); }
    catch (const std::exception& error) {
        if (preserved) fail(std::string("Previous ROM preserved in .invalid-backup; replacement failed: ")+error.what());
        throw;
    }
}

}

std::vector<std::uint8_t> read_rom_image(const std::filesystem::path& source) {
    std::ifstream input(source,std::ios::binary|std::ios::ate);
    if (!input) fail("Cannot open ROM input");
    const auto end=input.tellg();
    if (end<0 || static_cast<std::uintmax_t>(end)>max_archive_size)
        fail("ROM/ZIP input size exceeds the 64 MiB archive limit");
    const auto count=static_cast<std::size_t>(end);
    input.seekg(0);
    std::array<std::uint8_t,4> prefix{};
    input.read(reinterpret_cast<char*>(prefix.data()),std::min<std::size_t>(count,4));
    if (!input && count>=4) fail("Cannot read ROM input header");
    if (is_raw_magic(magic(prefix)) && count!=rom_size)
        fail("Unsupported raw ROM size: expected exactly 16 MiB");
    input.clear(); input.seekg(0);
    std::vector<std::uint8_t> bytes(count);
    if (count && !input.read(reinterpret_cast<char*>(bytes.data()),count)) fail("Cannot read complete ROM input");
    if (input.peek()!=std::char_traits<char>::eof()) fail("ROM input changed while reading");
    if (!is_raw_magic(magic(bytes))) bytes=read_zip(bytes);
    auto canonical=rom_detail::normalize_byte_order(bytes);
    validate_canonical(canonical);
    return canonical;
}

void write_rom_exclusive(const std::filesystem::path& destination,
                         std::span<const std::uint8_t> canonical) {
    validate_canonical(canonical);
    rom_detail::write_bytes_exclusive(destination,canonical);
}

void ensure_rom_storage(const std::filesystem::path& destination,
                        std::span<const std::uint8_t> canonical) {
    // An invalid selected input cannot create even a lock or backup file.
    validate_canonical(canonical);
    // Storage is consumed as raw bytes by the runtime: an archive or swapped
    // image that normalizes correctly is still a different physical file.
    // Compare exact canonical bytes; preserve any other representation first.
    rom_detail::ensure_bytes_storage(destination,canonical);
}

}
