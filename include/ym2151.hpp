#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

// Original, specification-based functional model. NOT a cycle-exact core.
namespace independent_opm {
namespace detail {
// User-specified provisional recurrence; not verified against hardware.
// bit0 is LSB. Shift right, feed bit0 XOR bit3 into bit16.
constexpr std::uint32_t lfsr17_step(std::uint32_t state) noexcept {
    const std::uint32_t feedback = (state ^ (state >> 3)) & 1u;
    return ((state >> 1) | (feedback << 16)) & 0x1ffffu;
}
// Timing and waveform interpretation: original X68Sound src020615 lfo.h.
// See THIRD_PARTY_NOTICES.txt. Native clock/64 adaptation.
struct LfoClock {
    unsigned elapsed = 0, fraction = 0;
    static unsigned period(std::uint8_t frequency) noexcept {
        unsigned exponent = 15 - frequency / 16;
        return 8u << (exponent ? exponent : 1);
    }
    void restart() noexcept { elapsed = 0; }
    unsigned tick(std::uint8_t frequency) noexcept {
        ++elapsed;
        if (elapsed < period(frequency)) return 0;
        elapsed = 0;
        const unsigned multiplier = frequency / 16 == 15 ? 2 : 1;
        const unsigned sum = fraction + (16 + frequency % 16) * multiplier;
        fraction = sum % 16;
        return sum / 16;
    }
};
struct LfoValue { int am; int pm; };
inline LfoValue lfo_value(unsigned waveform, unsigned index) noexcept {
    const unsigned i = index % 512;
    if (waveform == 2) {
        const int ramp = int(i % 128);
        int pitch = i % 256 < 128 ? ramp : 127 - ramp;
        if (i >= 256) pitch = -pitch;
        return {i < 256 ? 255-int(i) : int(i)-256, pitch};
    }
    const int saw = int(i % 256);
    if (waveform == 1)
        return saw < 128 ? LfoValue{256,128} : LfoValue{0,-128};
    return {255-saw, saw < 128 ? saw : saw-255};
}

}

struct Stereo { double left = 0; double right = 0; };
enum class Envelope { off, attack, decay1, decay2, release };
struct OperatorInfo { double attenuation_db; double frequency_hz; Envelope stage; bool key; };

struct LfoInfo {
    std::uint16_t phase = 0, am = 0;
    std::int16_t pm = 0;
    double am_after_depth = 0, pm_after_depth = 0;
    bool uses_unverified_random = false;
};

class Ym2151 {
public:
    using Sink = void (*)(void*, Stereo);
    explicit Ym2151(std::uint32_t clock_hz = 3579545);
    void reset();
    // Integration API: immediate register update, bypasses BUSY rejection.
    void write_register(std::uint8_t address, std::uint8_t value);
    // Bus API: rejected writes have NO side effects. Address latch is instantaneous.
    void write_address(std::uint8_t address) { address_ = address; }
    bool write_data(std::uint8_t value);
    std::uint8_t status() const;
    bool irq() const { return (flags_ & 3) != 0; }
    std::uint8_t control_outputs() const { return registers_[0x1b] >> 6; }
    void advance(std::uint64_t clocks, Sink sink = nullptr, void* context = nullptr);
    Stereo last_sample() const { return last_; }
    std::uint64_t clock_count() const { return clocks_; }
    std::uint32_t clock_hz() const { return clock_hz_; }
    double native_rate() const { return clock_hz_ / 64.0; }
    double sample_fraction() const { return sample_phase_ / 64.0; }
    OperatorInfo inspect(unsigned channel, unsigned slot) const;
    LfoInfo inspect_lfo() const { return lfo_info_; }
    // Calibration model: output carriers may use the previous native sample.
    // Bits 0..3 are M1/M2/C1/C2 in register order. No automatic hardware mapping.
    // Applies only to audible carriers of the selected algorithm; FM routing is unchanged.
    void set_output_sample_delays(unsigned channel, std::uint8_t left_mask,
                                  std::uint8_t right_mask);
    void clear_output_sample_delays();
    // Recording-derived ALG5/ALG7 carrier frame selection; common capture delay excluded.
    // Other algorithms retain their existing output. Explicit masks take precedence.
    void set_measured_output_timing(bool enabled) { measured_alg5_timing_ = enabled; }
    // Compatibility alias; now enables the measured ALG5 and ALG7 models.
    void set_measured_alg5_timing(bool enabled) { set_measured_output_timing(enabled); }
    // All state is value-owned: copying the instance saves/restores exact state
    // within the same executable. No pointers/callbacks are retained.
private:
    struct Operator {
        std::uint32_t phase = 0;
        double attenuation = 96;
        Envelope stage = Envelope::off;
        bool key = false;
    };
    std::uint32_t clock_hz_;
    std::array<std::uint8_t, 256> registers_{};
    std::array<std::array<Operator, 4>, 8> operators_{};
    std::array<std::array<double, 2>, 8> feedback_{};
    std::array<std::uint8_t, 8> manual_keys_{};
    std::uint64_t clocks_ = 0;
    std::uint32_t timer_a_ = 0, timer_b_ = 0, busy_ = 0;
    unsigned sample_phase_ = 0;
    std::uint8_t address_ = 0, flags_ = 0, amd_ = 0, pmd_ = 0;
    std::uint16_t lfo_phase_ = 0;
    detail::LfoClock lfo_clock_{};
    double noise_phase_ = 0;
    LfoInfo lfo_info_{};
    std::uint32_t noise_state_ = 1, lfo_lfsr_ = 1;
    std::uint8_t random_code_ = 0;
    bool csm_release_ = false;
    Stereo last_{};
    std::array<std::uint8_t, 8> left_previous_mask_{}, right_previous_mask_{};
    bool measured_alg5_timing_ = false;
    std::array<std::array<double, 4>, 8> previous_outputs_{};
    unsigned reg(unsigned base, unsigned channel, unsigned slot) const;
    unsigned rate(unsigned channel, unsigned slot, unsigned raw) const;
    double frequency(unsigned channel, unsigned slot, double cents) const;
    std::uint32_t period_a() const;
    std::uint32_t period_b() const;
    void key(unsigned channel, unsigned slot, bool on, bool force = false);
    void envelope(unsigned channel, unsigned slot);
    Stereo synthesize();
};

// Causal 33-tap windowed-sinc output filter; delay = 16 native samples.
// It is a host-side resampler, not a model of YM3012 or the analog output stage.
class Resampler {
public:
    Resampler(double native_rate, std::uint32_t output_rate);
    void push(Stereo frame);
    Stereo output(double native_fraction) const;
    static void receive(void* context, Stereo frame) {
        static_cast<Resampler*>(context)->push(frame);
    }
private:
    static constexpr unsigned taps = 33, phases = 1024;
    std::array<Stereo, taps> history_{};
    std::array<std::array<double, taps>, phases> weights_{};
    unsigned head_ = 0;
};
}
