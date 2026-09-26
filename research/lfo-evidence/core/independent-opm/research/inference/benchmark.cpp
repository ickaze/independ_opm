// SPDX-License-Identifier: 0BSD
// Copyright (C) 2026 by I.C.KaZe
#include "ym2151.hpp"
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
using namespace independent_opm::detail;
volatile std::uint32_t result_sink;
static std::array<std::uint32_t,131072> table;
template<class F> void run(const char* name,F fn) {
    constexpr unsigned count=10000000;
    double best=1e30;std::uint32_t final=0;
    for(unsigned repeat=0;repeat<3;++repeat){
        auto a=std::chrono::steady_clock::now();std::uint32_t s=1;
        for(unsigned i=0;i<count;++i)s=fn(s);
        auto b=std::chrono::steady_clock::now();result_sink=s;final=s;
        const double ns=std::chrono::duration<double,std::nano>(b-a).count()/count;
        if(ns<best)best=ns;
    }
    std::cout<<name<<","<<best<<","<<final<<"\n";
}
int main(){
 for(unsigned s=0;s<table.size();++s)table[s]=sequence_advance16(s);
 std::cout<<"method,best_ns_per_16_updates,final_state\n";
 run("loop16",[](unsigned s){for(unsigned n=0;n<16;++n)s=sequence_step(s);return s;});
 run("direct16",[](unsigned s){return sequence_advance16(s);});
 run("direct16_two_masks",[](unsigned s){unsigned q=s^(s>>3);return (s>>16)^((q<<1)&0x1ffffu)^((q&3u)<<15);});
 run("table_512KiB",[](unsigned s){return table[s];});
}
