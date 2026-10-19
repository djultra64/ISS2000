"""Original project work: djultra64. Execute the emitted target-growth block.

Removing its synchronization must let growth finish while the presenter owns
interpolatedMutex. No game/GPU run and no intentional C++ data race is needed.
"""
from pathlib import Path
import importlib.util
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = r'''
#include <chrono>
#include <cstdio>
#include <future>
#include <memory>
#include <mutex>
#include <thread>
#include <vector>
#include <cstdint>
using namespace std::chrono_literals;
struct Framebuffer { enum class Type { Color }; };
struct RenderMultisampling {};
struct RenderTarget {
    RenderTarget(uint32_t, Framebuffer::Type, RenderMultisampling, bool) {}
};
struct Shared {
    std::mutex interpolatedMutex;
    std::vector<std::unique_ptr<RenderTarget>> interpolatedColorTargets;
    struct { struct { unsigned sampleCount = 1; } multisampling; bool usesHDR = false; } renderTargetManager;
};
struct { Shared *sharedResources; } ext;
int main() {
    Shared shared;
    ext.sharedResources = &shared;
    auto &targets = shared.interpolatedColorTargets;
    targets.emplace_back(std::make_unique<RenderTarget>(7, Framebuffer::Type::Color, RenderMultisampling(), false));
    RenderTarget *oldTarget = targets[0].get();
    // Force a reallocation regardless of this library's initial vector capacity.
    const uint32_t displayFrames = uint32_t(targets.capacity()) + 2;
    const bool generateInterpolatedFrames = true;
    struct { uint32_t address = 7; } interpolationTargetKey;
    std::promise<void> attempted, finished;
    auto started = attempted.get_future();
    auto done = finished.get_future();
    std::unique_lock presenterLock(shared.interpolatedMutex);
    std::thread producer([&] {
        attempted.set_value();
        GROWTH_BLOCK
        finished.set_value();
    });
    started.wait();
    // The existing presenter uses this same mutex while indexing the vector.
    // Growth cannot complete before that access releases ownership.
    bool escaped = done.wait_for(100ms) == std::future_status::ready;
    presenterLock.unlock();
    producer.join();
    if (escaped) {
        std::fprintf(stderr, "TARGET VECTOR GREW WHILE PRESENTATION OWNED ITS MUTEX\n");
        return 22;
    }
    if (targets.size() != displayFrames - 1 || targets[0].get() != oldTarget) return 23;
    for (const auto &target : targets) if (!target) return 24;
    // Scope must end before any later producer wait/GPU work.
    if (!shared.interpolatedMutex.try_lock()) return 25;
    shared.interpolatedMutex.unlock();
    return 0;
}
'''


class TargetVectorGrowthTests(unittest.TestCase):
    def test_emitted_growth_excludes_presenter_vector_access(self):
        source = ROOT / '.local/deps/rt64/src/hle/rt64_workload_queue.cpp'
        if not source.is_file():
            self.skipTest('Pinned RT64 source required')
        path = ROOT / 'tools/prepare_rt64_menu_interpolation.py'
        spec = importlib.util.spec_from_file_location('target_growth_generator', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = source.read_bytes()
        # Baseline verifies this harness detects the old missing barrier.
        variants = [('upstream', raw.decode(), 22)]
        variants += [('evidence' if evidence else 'production', module.derive(raw, evidence).decode(), 0)
                     for evidence in (False, True)]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for label, text, expected in variants:
                with self.subTest(variant=label):
                    begin = text.index('                // Create as many render targets as required')
                    end = text.index('                const int64_t originalTimeMicro', begin)
                    unit = folder / (label + '.cpp')
                    executable = folder / label
                    unit.write_text(CODE.replace('GROWTH_BLOCK', text[begin:end]))
                    build = subprocess.run(['c++', '-std=c++20', '-pthread', str(unit), '-o', str(executable)], capture_output=True, text=True)
                    self.assertEqual(build.returncode, 0, build.stderr)
                    result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, expected, result.stderr)
                    if expected:
                        self.assertIn('TARGET VECTOR GREW WHILE PRESENTATION OWNED ITS MUTEX', result.stderr)


if __name__ == '__main__':
    unittest.main()
