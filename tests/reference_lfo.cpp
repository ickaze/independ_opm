// Optional comparison with the user-supplied original source; not part of CMake.
#include "ym2151.hpp"
#include <iostream>
#include <cstdlib>
#include <cstdint>
constexpr int N_CH=8;
int Samprate=62500;
std::uint32_t irnd(){return 0;} // Random source deliberately excluded from comparison.
#include "original_lfo.h"
int main(){
 using namespace independent_opm;
 for(unsigned w=0;w<3;w++)for(unsigned f=0;f<256;f++){
  Lfo ref;ref.Init();ref.SetLFRQ(f);ref.SetWaveForm(w);ref.SetPMDAMD(127);ref.SetPMDAMD(255);ref.SetPMSAMS(0,0x51);
  detail::LfoClock clock;unsigned phase=0;
  const unsigned count=detail::LfoClock::period(f)*32;
  for(unsigned n=0;n<count;n++){
   ref.Update();unsigned step=clock.tick(f);phase=(phase+step*(w==2?2:1))%512;
   auto v=detail::lfo_value(w,phase);
   const int am=v.am*127/128;
   const int pm=(v.pm<0?-1:1)*(std::abs(v.pm)*127*16/4096);
   if(ref.GetAmValue(0)!=am || ref.GetPmValue(0)!=pm){std::cerr<<"mismatch "<<w<<" "<<f<<" "<<n<<"\n";return 1;}
  }
 }
 std::cout<<"PASS: original lfo.h, 256 frequencies x 3 periodic waveforms, 32 update events each; channel scaling compared separately from core adapter\n";
}
