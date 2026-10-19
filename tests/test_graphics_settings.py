"""Native graphics settings persistence; no game execution or rendering claim."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
JSON_INCLUDE = Path(os.environ.get('ISS2000_JSON_INCLUDE',ROOT/'.local/deps/N64ModernRuntime/thirdparty'))

class GraphicsSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('c++') or not (JSON_INCLUDE/'json/json.hpp').is_file():
            raise unittest.SkipTest('graphics settings tests require C++20 and the pinned nlohmann JSON header')
        cls.build=tempfile.TemporaryDirectory(prefix='iss2000-graphics-test-')
        cls.folder=Path(cls.build.name)
        (cls.folder/'main.cpp').write_text(r'''
#include "runtime/graphics_settings.hpp"
#include <iostream>
#include <iterator>
#include <fstream>
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#endif
int main(int argc,char** argv){
 try {
  std::string mode=argv[1];
  if(mode=="load") std::cout<<iss2000::serialize_graphics_settings(iss2000::load_graphics_settings(argv[2]));
  else {
   std::string input{std::istreambuf_iterator<char>(std::cin),{}};
   auto s=iss2000::parse_graphics_settings(input);
   if(mode=="collision") {
#ifdef _WIN32
    auto pid=GetCurrentProcessId();
#else
    auto pid=getpid();
#endif
    auto collision=std::filesystem::path(argv[2])/(".graphics.json.tmp."+std::to_string(pid)+".0");
    {std::ofstream out(collision);out<<"preserve collision";}
    iss2000::save_graphics_settings(argv[2],s);
    std::ifstream in(collision);std::cout<<in.rdbuf();
   } else if(mode=="invalid-enum") {
    s.resolution=static_cast<iss2000::RenderResolution>(123);
    iss2000::save_graphics_settings(argv[2],s);
   } else if(mode=="save") iss2000::save_graphics_settings(argv[2],s);
   else if(mode=="label") std::cout<<iss2000::resolution_label(s);
   else if(mode=="height") std::cout<<iss2000::target_height(s);
   else if(mode=="scale") std::cout<<(argc>3?iss2000::resolution_multiplier(s,static_cast<std::uint32_t>(std::stoul(argv[3]))):iss2000::resolution_multiplier(s));
   else std::cout<<iss2000::serialize_graphics_settings(s);
  }
 }catch(const std::exception& e){std::cerr<<e.what();return 1;}
}
''')
        cls.binary=cls.folder/'settings'
        subprocess.run(['c++','-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-I'+str(ROOT/'src'),'-I'+str(JSON_INCLUDE),str(cls.folder/'main.cpp'),
                        str(ROOT/'src/runtime/graphics_settings.cpp'),'-o',str(cls.binary)],
                       check=True,capture_output=True,text=True)
    @classmethod
    def tearDownClass(cls):cls.build.cleanup()
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='iss2000-graphics-input-')
        self.addCleanup(self.temp.cleanup);self.data=Path(self.temp.name)
    def settings(self,**kw):return dict(schemaVersion=1,aspectRatio='4:3',resolution='Original',refreshRate='Original',**kw)
    def run_native(self,mode,value=None):
        return subprocess.run([str(self.binary),mode,str(self.data)],input=json.dumps(value) if isinstance(value,dict) else value,
                              capture_output=True,text=True,timeout=10)
    def test_missing_settings_defaults_without_creating_files(self):
        r=self.run_native('load');self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout),dict(self.settings(),aspectRatio="16:9",resolution="720",refreshRate="60"));self.assertEqual(list(self.data.iterdir()),[])
    def test_fullscreen_roundtrip_preserves_legacy_settings_and_rejects_invalid_types(self):
        legacy=self.settings()
        self.assertEqual(self.run_native('parse',legacy).returncode,0)
        fullscreen=dict(legacy,fullscreen=True)
        result=self.run_native('save',fullscreen)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(self.run_native('load').stdout),fullscreen)
        for invalid in ['yes',1,None]:
            result=self.run_native('parse',dict(legacy,fullscreen=invalid))
            self.assertNotEqual(result.returncode,0)
        self.assertEqual(self.run_native('save',legacy).returncode,0)
        self.assertEqual(json.loads(self.run_native('load').stdout),legacy)

    def test_all_supported_options_roundtrip_and_resolution_scale(self):
        for aspect in ['4:3','16:9']:
            for resolution,height in [('Original',240),('720',720),('900',900),('1080',1080),('1440',1440),('1800',1800),('2160',2160)]:
                for refresh in ['Original','60','120']:
                    v=self.settings();v.update(aspectRatio=aspect,resolution=resolution,refreshRate=refresh)
                    r=self.run_native('parse',v);self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout),v)
                    r=self.run_native('scale',v);self.assertEqual(float(r.stdout),height/240)
    def test_resolution_labels_match_selected_aspect_and_original(self):
        for height in [720,900,1080,1440,1800,2160]:
            for aspect,width in [('16:9',height*16//9),('4:3',height*4//3)]:
                settings=dict(self.settings(),resolution=str(height),aspectRatio=aspect)
                result=self.run_native('label',settings)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(result.stdout,f'{height}p ({width} x {height})')
        for aspect in ['16:9','4:3']:
            result=self.run_native('label',dict(self.settings(),aspectRatio=aspect))
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(result.stdout,'Original')

    def test_strict_schema_rejects_malformed_wrong_types_unknown_and_duplicate_fields(self):
        good=self.settings()
        values=['{','[]','null','{}',json.dumps(good).replace('"schemaVersion": 1','"schemaVersion": 1.0'),
                json.dumps(good).replace('"schemaVersion": 1','"schemaVersion": true'),
                json.dumps(good)[:-1]+',"resolution":"720"}']
        for field,bad in [('schemaVersion',2),('aspectRatio','21:9'),('resolution','4K'),('refreshRate',144),('home','/tmp')]:
            v=dict(good);v[field]=bad;values.append(json.dumps(v))
        for value in values:
            r=self.run_native('parse',value);self.assertNotEqual(r.returncode,0,value)
    def test_2d_filter_roundtrip_and_legacy_default(self):
        legacy=self.settings()
        self.assertEqual(json.loads(self.run_native('parse',legacy).stdout),legacy)
        filtered=dict(legacy,filter2D='Bilinear')
        for fullscreen in [False,True]:
            value=dict(filtered,**({'fullscreen':True} if fullscreen else {}))
            result=self.run_native('save',value)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(self.run_native('load').stdout),value)
        for invalid in ['Linear','On',1,True,None]:
            self.assertNotEqual(self.run_native('parse',dict(legacy,filter2D=invalid)).returncode,0)
        result=self.run_native('parse',dict(legacy,filter2D='Original'))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout),legacy)

    def test_malformed_existing_is_reported_and_preserved(self):
        path=self.data/'graphics.json';path.write_text('{broken')
        r=self.run_native('load');self.assertNotEqual(r.returncode,0);self.assertEqual(path.read_text(),'{broken')
    def test_save_replaces_settings_only_and_loads_persisted_values(self):
        old=self.settings();self.assertEqual(self.run_native('save',old).returncode,0)
        sentinel=self.data/'keep.bin';sentinel.write_bytes(b'preserve')
        new=dict(old,aspectRatio='16:9',resolution='2160',refreshRate='120')
        r=self.run_native('save',new);self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(self.run_native('load').stdout),new)
        self.assertEqual(sentinel.read_bytes(),b'preserve');self.assertEqual(sorted(p.name for p in self.data.iterdir()),['graphics.json','keep.bin'])
    def test_invalid_selected_settings_never_mutate_existing_file(self):
        path=self.data/'graphics.json';path.write_bytes(b'existing')
        r=self.run_native('save',dict(self.settings(),resolution='no'))
        self.assertNotEqual(r.returncode,0);self.assertEqual(path.read_bytes(),b'existing')
    def test_symlink_settings_and_symlink_folder_are_rejected_without_touching_target(self):
        if os.name=='nt':self.skipTest('symlink creation requires Windows privileges')
        target=self.data/'original';target.write_bytes(b'preserve');(self.data/'graphics.json').symlink_to(target)
        for mode in ['load','save']:
            r=self.run_native(mode,self.settings());self.assertNotEqual(r.returncode,0)
        self.assertEqual(target.read_bytes(),b'preserve');(self.data/'graphics.json').unlink()
        real=self.data/'real';real.mkdir();link=self.data/'link';link.symlink_to(real,target_is_directory=True)
        self.data=link;r=self.run_native('save',self.settings());self.assertNotEqual(r.returncode,0);self.assertEqual(list(real.iterdir()),[])
    def test_directory_collision_preserves_contents_and_cleans_temporary_files(self):
        path=self.data/'graphics.json';path.mkdir();(path/'keep').write_bytes(b'safe')
        r=self.run_native('save',self.settings());self.assertNotEqual(r.returncode,0)
        self.assertEqual((path/'keep').read_bytes(),b'safe');self.assertEqual(list(self.data.iterdir()),[path])
    def test_oversized_input_rejected(self):
        r=self.run_native('parse',' '*65537+json.dumps(self.settings()));self.assertNotEqual(r.returncode,0)

    def test_exclusive_temporary_collision_preserves_existing_file(self):
        r=self.run_native('collision',self.settings());self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(r.stdout,'preserve collision')
        self.assertEqual(json.loads((self.data/'graphics.json').read_text()),self.settings())
    def test_invalid_native_enum_rejected_before_mutation(self):
        original=self.data/'graphics.json';original.write_bytes(b'original')
        r=self.run_native('invalid-enum',self.settings());self.assertNotEqual(r.returncode,0)
        self.assertEqual(original.read_bytes(),b'original')
    def test_concurrent_publish_leaves_complete_valid_settings(self):
        options=[dict(self.settings(),resolution=r) for r in ['720','900','1080','1440','1800','2160']]
        processes=[]
        for i in range(16):
            p=subprocess.Popen([str(self.binary),'save',str(self.data)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            processes.append((p,options[i%len(options)]))
        results=[]
        for p,value in processes:
            _,error=p.communicate(json.dumps(value),timeout=10);results.append((p.returncode,error))
        for code,error in results:self.assertEqual(code,0,error)
        self.assertIn(json.loads((self.data/'graphics.json').read_text()),options)
        self.assertEqual([p.name for p in self.data.iterdir()],['graphics.json'])

    def test_requested_resolution_tracks_actual_native_height(self):
        for resolution,height in [('Original',0),('720',720),('900',900),('1080',1080),('1440',1440),('1800',1800),('2160',2160)]:
            settings=dict(self.settings(),resolution=resolution)
            requested=self.run_native('height',settings)
            self.assertEqual(requested.returncode,0,requested.stderr)
            self.assertEqual(int(requested.stdout),height)
            for native in [0,240,480]:
                result=subprocess.run([str(self.binary),'scale',str(self.data),str(native)],input=json.dumps(settings),capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                self.assertEqual(float(result.stdout),height/(native or 240) if height else 1.)

class GraphicsSettingsDependencyTests(unittest.TestCase):
    def test_missing_pinned_dependency_is_reported_as_skip(self):
        with tempfile.TemporaryDirectory() as missing:
            env=dict(os.environ,ISS2000_JSON_INCLUDE=missing)
            result=subprocess.run([sys.executable,'-m','unittest','tests.test_graphics_settings.GraphicsSettingsTests','-v'],cwd=ROOT,env=env,capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('skipped',result.stderr);self.assertIn('Ran 0 tests',result.stderr)
        self.assertIn('pinned nlohmann JSON header',result.stderr)

