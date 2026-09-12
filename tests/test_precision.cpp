#include "ym2151.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace independent_opm;
void check(bool condition,const char* message) { if(!condition) throw std::runtime_error(message); }
// Independent published-time checks: do not import the implementation's time table.
void attack(unsigned raw,unsigned kc,double milliseconds) {
    Ym2151 c(3600000);
    c.write_register(0x28,static_cast<std::uint8_t>(kc));
    c.write_register(0x80,static_cast<std::uint8_t>(192|raw));
    c.write_register(8,8);
    unsigned samples=0;
    while(c.inspect(0,0).stage==Envelope::attack && samples<1000000) { c.advance(64); ++samples; }
    double measured=samples*64.0/3600000*1000;
    check(std::abs(measured-milliseconds)<=64.0/3600000*1000+1e-8,"published attack time");
}
int main() {
 try {
    // A complete nonzero orbit checks width, taps and absence of short cycles.
    std::uint32_t state=1;
    check(detail::lfsr17_step(1)==0x10000u,"LFSR bit0 feeds bit16");
    check(detail::lfsr17_step(8)==0x10004u,"LFSR bit3 feeds bit16");
    check(detail::lfsr17_step(9)==4u,"LFSR taps XOR, not OR");
    for(unsigned step=1;step<=131071;++step) {
        state=detail::lfsr17_step(state);
        check(state>0 && state<=0x1ffffu,"LFSR range/nonzero");
        check((state==1)==(step==131071),"LFSR full period");
    }

    for(unsigned freq=0;freq<256;freq++) {
        detail::LfoClock timer;
        const unsigned interval = freq < 240 ? 262144u/(1u<<(freq/16)) : 16;
        unsigned total=0;
        for(unsigned n=1;n<=interval*16;n++) {
            auto step=timer.tick(static_cast<std::uint8_t>(freq));
            check(bool(step)==(n%interval==0),"update boundary");total+=step;
        }
        check(total==(16+freq%16)*(freq>=240?2:1),"fractional rate");
    }
    Ym2151 chip(4000000);chip.advance(6400);chip.write_register(0x18,240);
    chip.advance(15*64);check(chip.inspect_lfo().phase==0,"frequency write clears elapsed");
    chip.advance(64);check(chip.inspect_lfo().phase==2,"highest octave doubles advance");
    chip.advance(5*64);chip.write_register(0x18,240);
    chip.advance(15*64);check(chip.inspect_lfo().phase==2,"same value restarts");
    chip.advance(64);check(chip.inspect_lfo().phase==4,"restarted boundary");
    chip.advance(5*64);chip.write_register(1,2);chip.advance(6400);
    check(chip.inspect_lfo().phase==0,"hold phase zero");chip.write_register(1,0);
    chip.advance(10*64);check(chip.inspect_lfo().phase==0,"retain partial timer");
    chip.advance(64);check(chip.inspect_lfo().phase==2,"resume partial timer");
    const int points[][4]={{0,127,128,127},{0,128,127,-127},
      {1,0,256,128},{1,128,0,-128},{2,127,128,127},
      {2,128,127,127},{2,255,0,0},{2,256,0,0},{2,383,127,-127},{2,511,255,0}};
    for(auto& p:points){auto v=detail::lfo_value(p[0],p[1]);check(v.am==p[2]&&v.pm==p[3],"waveform endpoint");}
    Ym2151 square;square.write_register(0x1b,1);square.write_register(0x19,127);square.advance(64);
    check(square.inspect_lfo().am==256&&square.inspect_lfo().am_after_depth==254,"square width/depth");
    Ym2151 tri;tri.write_register(0x18,240);tri.write_register(0x1b,2);tri.advance(16*64);
    check(tri.inspect_lfo().phase==4,"triangle advances twice");
    Ym2151 random;random.write_register(0x18,255);random.write_register(0x1b,3);
    auto expected=1u;
    for(unsigned i=0;i<512;i++){
        random.advance(16*64);expected=detail::lfsr17_step(expected);
        check(random.inspect_lfo().phase==(expected%512),"one provisional random step per event");
    }
    check(random.inspect_lfo().uses_unverified_random,"unverified random flag");
    auto copy=random;random.advance(123456);for(unsigned n=0;n<123456;n++)copy.advance(1);
    check(random.inspect_lfo().phase==copy.inspect_lfo().phase,"copy/chunk independence");
    attack(2,0,7723.38);attack(2,12,4354.31);attack(12,0,249.17);
    attack(24,0,3.89);attack(30,0,.51);attack(30,12,0);
    std::cout<<"PASS: 256 frequency cadences, register restarts, reset hold/resume, waveform endpoints, random/state, envelope times\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
