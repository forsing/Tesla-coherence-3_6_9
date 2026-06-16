#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
SRBIN Nikola Tesla, za sva vremena, najveci naucnik sveta.

SERBIAN Nikola Tesla, for all time, the greatest scientist in the world.
"""

"""
Glavni motor je koherencija, 
a CSV frekvencija samo stabilizuje izbor.
"""


import numpy as np
import importlib
import matplotlib

for _mod, _bk in (("PyQt5", "QtAgg"), ("PySide6", "QtAgg"), ("tkinter", "TkAgg")):
    try:
        importlib.import_module(_mod)
        matplotlib.use(_bk)
        break
    except Exception:
        continue
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import LogNorm
import pandas as pd
import csv as _csv
from pathlib import Path as _Path
# =============================================================================
# HARMONIC MAGIC NUMBERS (proton/neutron shell closures)
# =============================================================================
MAGIC_NUMBERS = np.array([2, 8, 20, 28, 50, 82, 126, 184, 258, 318, 400])
# =============================================================================
# COHERENCE SCORE – Complete Implementation
# =============================================================================

def coherence_score(Z, N, anchor_hz, ratio_19_13, cutoff_hz, exponent_n,
branch_mix, t3_coupling):
 """
 Compute harmonic coherence for a nucleus (Z,N) based on GUT parameters.
 branch_mix: +1 = pure matter branch (n positive)
 -1 = pure antimatter branch (n negative)
 0 = pure T3 (dark matter branch) – then t3_coupling matters
 t3_coupling: 0..1 – how much T3 admixture (dark matter component)
 Returns coherence in [0,1].
 """
 A = Z + N # mass number
 # 1) Resonance term: product of scaled frequencies aligns with integer multiples of anchor
 f_scale = A * anchor_hz / 27.0
 resonance = np.exp(-5.0 * np.abs(f_scale - np.round(f_scale)))
 # 2) Magic number proximity (normalised)
 Z_magic_dist = np.min(np.abs(Z - MAGIC_NUMBERS)) / 40.0
 N_magic_dist = np.min(np.abs(N - MAGIC_NUMBERS)) / 40.0
 # 3) 19:13 ratio penalty (ideal Z/N)
 if N > 0:
    ratio = Z / N
    ratio_penalty = np.abs(ratio - ratio_19_13) / ratio_19_13
 else:
    ratio_penalty = 1.0


 
 # 4) 230th subharmonic cutoff penalty (applies to all branches, but for T3 we adjust later)
 n_eff = A / 230.0
 n_penalty = np.exp(-10.0 * np.abs(n_eff - np.round(n_eff)))
 # 5) Dimensional exponent resonance (depends on branch)
 n_val = np.log(A + 1.0) / np.log(anchor_hz) if anchor_hz > 1 else 0.0
 # Matter branch (T1)
 if branch_mix >= 0.5:
    n_target = exponent_n
    n_res = np.exp(-2.0 * np.abs(np.sin(np.pi * (n_val - n_target))))
 # Anti-matter branch (T2)
 elif branch_mix <= -0.5:
    n_target = -exponent_n
    n_res = np.exp(-2.0 * np.abs(np.sin(np.pi * (n_val - n_target))))
 # Dark matter branch (T3) – uses shifted target and its own cutoff
 else:
    # Shifted target for T3: exponent_n * (13/19)
    n_target_T3 = exponent_n * (13.0 / 19.0)
    n_res = np.exp(-2.0 * np.abs(np.sin(np.pi * (n_val - n_target_T3))))
    # For T3 we also replace the 230th cutoff penalty with a T3-specific one
    # T3 cutoff frequency: f_c3 = anchor_hz * (13/19) / 230
    f_c3 = anchor_hz * (13.0 / 19.0) / 230.0
    # Effective frequency scale for T3 (use A times f_c3 / anchor? Simpler:)
    # We use the same n_eff but scaled by (13/19) because T3 cutoff is smaller
    n_eff_T3 = A * (13.0/19.0) / 230.0
    n_penalty = np.exp(-10.0 * np.abs(n_eff_T3 - np.round(n_eff_T3)))
 
 # Combine all terms 
 coherence = resonance * n_penalty * n_res * np.exp(- (Z_magic_dist + N_magic_dist + ratio_penalty))
 # Apply T3 coupling if in mixed regime
 if t3_coupling > 0 and abs(branch_mix) < 0.5:
    # Dark matter contribution: modify coherence by a factor that depends on t3_coupling t3_coupling
    coherence = coherence * (1.0 - t3_coupling) + t3_coupling * 0.8 # 0.8 is empirical scaling is empirical scaling
 return np.clip(coherence, 0.0, 1.0)

# Half-life calibration (Tennessine-294: Z=117, N=177, coherence≈0.45, half-life 0.08 s)
def half_life_from_coherence(coh, ref_coh=0.45, ref_hl=0.08, beta=8.0):
 safe_coh = max(1e-6, min(0.999999, coh))
 log_hl = np.log(ref_hl) + beta * (safe_coh - ref_coh) / (1.0 - safe_coh + 1e-6)
 return np.exp(log_hl)







# =============================================================================
# QUANTUM HANDSHAKE CLASSES
# =============================================================================
class QuantumHandshakeT1T2:
    """
    Handshake between matter (T1) and anti-matter (T2) at 230th subharmonic.
    """
    def __init__(self, freq_hz=0.1174, phase_offset_deg=-1.0):
        self.carrier_freq = freq_hz
        self.phase_offset = np.radians(phase_offset_deg)
        self.t1_phase = 0.0
        self.locked = False
        self.energy_extracted = 0.0
 
    def update(self, dt, t2_feedback_phase, coupling=0.5):
        error = (t2_feedback_phase - self.t1_phase - self.phase_offset) % (2*np.pi)
        if error > np.pi:
            error -= 2*np.pi
        self.t1_phase += coupling * error * dt
        self.locked = abs(error) < 0.01
        if self.locked:
            energy = 10000.0 * max(0.0, t2_feedback_phase) * dt # amplification factor is 10000.0
            self.energy_extracted += energy
        return self.t1_phase
 

class QuantumHandshakeT1T3:
 """
 Handshake between matter (T1) and dark matter (T3) at dark resonance frequency.
 """
 def __init__(self, freq_hz=0.080, phase_offset_deg=-2.0):
    self.carrier_freq = freq_hz
    self.phase_offset = np.radians(phase_offset_deg)
    self.t1_phase = 0.0
    self.locked = False
    self.energy_extracted = 0.0
 
 def update(self, dt, t3_feedback_phase, coupling=0.3):
    error = (t3_feedback_phase - self.t1_phase - self.phase_offset) % (2*np.pi)
    if error > np.pi:
        error -= 2*np.pi
    self.t1_phase += coupling * error * dt
    self.locked = abs(error) < 0.01
    if self.locked:
        energy = 1000.0 * max(0.0, t3_feedback_phase) * dt # lower coupling
        self.energy_extracted += energy
    return self.t1_phase



# =============================================================================
# GRID DEFINITION (Z from 100 to 184, N from 140 to 400)
# =============================================================================
Z_vals = np.arange(100, 185, 2, dtype=np.float64)
N_vals = np.arange(140, 401, 2, dtype=np.float64)
extent = [N_vals[0], N_vals[-1], Z_vals[0], Z_vals[-1]]
# Default parameters
anchor_default = 27.0
ratio_default = 19.0 / 13.0
cutoff_default = anchor_default / 230.0
n_default = 3.54
branch_default = 1.0 # matter branch
t3_default = 0.0
# Initial coherence map (matter branch)
coherence_init = np.zeros((len(Z_vals), len(N_vals)))
for i, Z in enumerate(Z_vals):
    for j, N in enumerate(N_vals):
        coherence_init[i, j] = coherence_score(Z, N, anchor_default, ratio_default,
        cutoff_default, n_default, branch_default, t3_default)
        




# =============================================================================
# CREATE MAIN INTERACTIVE FIGURE
# =============================================================================
fig, ax = plt.subplots(figsize=(12, 8))
try:
    fig.canvas.manager.set_window_title('Tesla_predictiv_v16')
except Exception:
    pass
plt.subplots_adjust(bottom=0.45, left=0.1) # space for sliders and buttons
im = ax.imshow(coherence_init, origin='lower', aspect='auto', cmap='hot_r',
 extent=extent, norm=LogNorm(vmin=0.001, vmax=1))
cbar = plt.colorbar(im, ax=ax, label='Harmonic Coherence (higher = more stable)')
# Mark magic numbers
for m in MAGIC_NUMBERS:
 if m >= Z_vals.min() and m <= Z_vals.max():
  ax.axhline(y=m, color='cyan', linestyle='--', linewidth=0.8, alpha=0.6)
 if m >= N_vals.min() and m <= N_vals.max():
  ax.axvline(x=m, color='cyan', linestyle='--', linewidth=0.8, alpha=0.6)
# Highlight predicted islands (matter side)
ax.scatter([184], [126], color='lime', s=100, marker='*', label='Island: Z=126,N=184')
ax.scatter([184], [120], color='yellow', s=80, marker='^', label='Z=120,N=184')
ax.scatter([196], [126], color='cyan', s=80, marker='s', label='Z=126,N=196')
ax.scatter([318], [164], color='orange', s=100, marker='D', label='Z=164,N=318')
ax.legend(loc='upper left')
ax.set_xlabel('Neutron Number (N)')
ax.set_ylabel('Proton Number (Z)')
ax.grid(alpha=0.3)
ax.set_title(f'[v16] Harmonic Framework – Stability Islands (Matter Branch)\n'
 f'Anchor={anchor_default} Hz, Ratio={ratio_default:.4f}, '
 f'Cutoff={cutoff_default:.4f} Hz, n={n_default}', fontsize=14)
# -------------------------------------------------------------------------
# Sliders
# -------------------------------------------------------------------------
ax_freq = plt.axes([0.2, 0.38, 0.6, 0.03])
freq_slider = Slider(ax_freq, 'Anchor Freq (Hz)', 20.0, 34.0,
valinit=anchor_default, valstep=0.1)
ax_ratio = plt.axes([0.2, 0.32, 0.6, 0.03])
ratio_slider = Slider(ax_ratio, '19:13 Ratio', 1.30, 1.60,
valinit=ratio_default, valstep=0.001)
ax_cutoff = plt.axes([0.2, 0.26, 0.6, 0.03])
cutoff_slider = Slider(ax_cutoff, '230th Cutoff (Hz)', 0.05, 0.30,
valinit=cutoff_default, valstep=0.001)
ax_n = plt.axes([0.2, 0.20, 0.6, 0.03])
n_slider = Slider(ax_n, 'Exponent n', 0.0, 10.0, valinit=n_default,
valstep=0.01)
ax_branch = plt.axes([0.2, 0.14, 0.6, 0.03])
branch_slider = Slider(ax_branch, 'Branch (+1=matter, -1=anti, 0=T3 dark)',
-1.0, 1.0,
 valinit=branch_default, valstep=0.01)
ax_t3 = plt.axes([0.2, 0.08, 0.6, 0.03])
t3_slider = Slider(ax_t3, 'T3 Dark Coupling (0..1)', 0.0, 1.0,
valinit=t3_default, valstep=0.01)
def update(val):
 anchor = freq_slider.val
 ratio = ratio_slider.val
 cutoff = cutoff_slider.val
 n_exp = n_slider.val
 branch = branch_slider.val
 t3 = t3_slider.val
 new_coh = np.zeros((len(Z_vals), len(N_vals)))
 for i, Z in enumerate(Z_vals):
  for j, N in enumerate(N_vals):
    new_coh[i, j] = coherence_score(Z, N, anchor, ratio, cutoff, n_exp,
branch, t3)
 im.set_data(new_coh)
 if branch > 0.5:
    mode = "Matter Branch (T1, forward time)"
 elif branch < -0.5:
    mode = "Anti-Element Branch (T2, reverse time)"
 else:
    mode = f"Dark Matter Branch (T3, orthogonal time) – coupling={t3:.2f}"
 ax.set_title(f'[v16] Harmonic Framework – {mode}\n'
 f'Anchor={anchor:.1f} Hz, Ratio={ratio:.4f}, Cutoff={cutoff:.4f} Hz, n={n_exp:.2f}',
 fontsize=14)
 fig.canvas.draw_idle()
freq_slider.on_changed(update)
ratio_slider.on_changed(update)
cutoff_slider.on_changed(update)
n_slider.on_changed(update)
branch_slider.on_changed(update)
t3_slider.on_changed(update)
# Green markers for default values
def add_green_marker(slider, value, label):
 asl = slider.ax
 vmin, vmax = slider.valmin, slider.valmax
 norm = (value - vmin) / (vmax - vmin)
 asl.axvline(x=norm, ymin=0, ymax=1, color='green', linewidth=2, alpha=0.7)
 asl.text(norm, -0.6, label, transform=asl.transAxes, ha='center', va='top',
color='green')
add_green_marker(freq_slider, anchor_default, '27 Hz')
add_green_marker(ratio_slider, ratio_default, '19/13')
add_green_marker(cutoff_slider, cutoff_default, f'{cutoff_default:.3f} Hz')
add_green_marker(n_slider, n_default, f'n={n_default}')
add_green_marker(branch_slider, branch_default, 'Matter (+1)')
add_green_marker(t3_slider, t3_default, 'T3=0')
# =============================================================================
# BUTTON: SIDE-BY-SIDE COMPARISON (T1, T2, T3)
# =============================================================================
ax_compare = plt.axes([0.05, 0.02, 0.18, 0.04])
compare_btn = Button(ax_compare, 'Compare T1/T2/T3', color='lightgray',
hovercolor='yellow')
def show_comparison(event):
 anchor = freq_slider.val
 ratio = ratio_slider.val
 cutoff = cutoff_slider.val
 n_exp = n_slider.val
 t3 = t3_slider.val
 # T1 (matter)
 matter = np.zeros((len(Z_vals), len(N_vals)))
 for i, Z in enumerate(Z_vals):
   for j, N in enumerate(N_vals):
     matter[i, j] = coherence_score(Z, N, anchor, ratio, cutoff, n_exp,
1.0, t3_default)
 # T2 (anti-matter)
 anti = np.zeros((len(Z_vals), len(N_vals)))
 for i, Z in enumerate(Z_vals):
    for j, N in enumerate(N_vals):
         anti[i, j] = coherence_score(Z, N, anchor, ratio, cutoff, n_exp, -1.0, t3_default)
 # T3 (dark matter) – branch = 0
 dark = np.zeros((len(Z_vals), len(N_vals)))
 for i, Z in enumerate(Z_vals):
    for j, N in enumerate(N_vals):
        dark[i, j] = coherence_score(Z, N, anchor, ratio, cutoff, n_exp, 0.0, t3_default)
 fig2, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
 fig2.suptitle(f'[v16] Three Branches: Matter (T1) | Anti-Matter (T2) | Dark Matter (T3)\n'
 f'Anchor={anchor:.1f} Hz, Ratio={ratio:.4f}, Cutoff={cutoff:.4f} Hz, n={n_exp:.2f}',
 fontsize=12)
 im1 = ax1.imshow(matter, origin='lower', aspect='auto', cmap='hot_r',
 extent=extent, norm=LogNorm(vmin=0.001, vmax=1))
 ax1.set_title('Matter Branch (T1)')
 ax1.set_xlabel('Neutron Number N')
 ax1.set_ylabel('Proton Number Z')
 plt.colorbar(im1, ax=ax1, label='Coherence')
 im2 = ax2.imshow(anti, origin='lower', aspect='auto', cmap='hot_r',
 extent=extent, norm=LogNorm(vmin=0.001, vmax=1))
 ax2.set_title('Anti-Matter Branch (T2)')
 ax2.set_xlabel('Neutron Number N')
 plt.colorbar(im2, ax=ax2, label='Coherence')
 im3 = ax3.imshow(dark, origin='lower', aspect='auto', cmap='hot_r',
 extent=extent, norm=LogNorm(vmin=0.001, vmax=1))
 ax3.set_title('Dark Matter Branch (T3)')
 ax3.set_xlabel('Neutron Number N')
 plt.colorbar(im3, ax=ax3, label='Coherence')
 # Mark magic numbers on all three
 for axs in (ax1, ax2, ax3):
    for m in MAGIC_NUMBERS:
        if m >= Z_vals.min() and m <= Z_vals.max():
            axs.axhline(y=m, color='cyan', linestyle='--', alpha=0.6)
        if m >= N_vals.min() and m <= N_vals.max():
            axs.axvline(x=m, color='cyan', linestyle='--', alpha=0.6)
 plt.tight_layout()
 fig2.canvas.draw_idle()
 plt.figure(fig2.number)
 plt.show(block=False)
compare_btn.on_clicked(show_comparison)
# =============================================================================
# BUTTON: EXTENDED ANTI-ELEMENT TABLE (AND DARK MASS SPECTRUM)
# =============================================================================
ax_table = plt.axes([0.26, 0.02, 0.18, 0.04])
table_btn = Button(ax_table, 'Extended Table', color='lightgray',
hovercolor='yellow')
def show_extended_table(event):
 anchor = freq_slider.val
 ratio = ratio_slider.val
 cutoff = cutoff_slider.val
 n_exp = n_slider.val
 # Anti-branch (T2)
 anti_coh = np.zeros((len(Z_vals), len(N_vals)))
 for i, Z in enumerate(Z_vals):
    for j, N in enumerate(N_vals):
         anti_coh[i, j] = coherence_score(Z, N, anchor, ratio, cutoff, n_exp, -1.0, 0.0)
 # Lokalni maksimumi rangirani po koherenciji (relativno, bez fiksnog praga 0.7
# jer apsolutna koherencija ovog modela retko prelazi taj nivo -> tabela bi bila prazna)
 peaks = []
 for i in range(1, len(Z_vals)-1):
    for j in range(1, len(N_vals)-1):
       c = anti_coh[i, j]
       if c > 0 and c >= anti_coh[i-1, j] and c >= anti_coh[i+1, j] \
          and c >= anti_coh[i, j-1] and c >= anti_coh[i, j+1]:
            Z = Z_vals[i]
            N = N_vals[j]
            hl = half_life_from_coherence(c)
            peaks.append((Z, N, c, hl))
 peaks.sort(key=lambda x: x[2], reverse=True)
 
 def element_name(Z):
    if Z <= 118:
        return f"Element {int(Z)}"
    digits = ['nil', 'un', 'bi', 'tri', 'quad', 'pent', 'hex', 'sept',
'oct', 'enn']
    name = ''.join(digits[int(d)] for d in str(int(Z))) + 'ium'
    return name.capitalize()
 print("\n" + "="*80)
 print("[v16] Extended Anti-Element Table (T2 Reverse Time Branch) – Coherence & Predicted Half-Life")
 print("="*80)
 print(f"{'Z':<5} {'N':<6} {'Element Name':<25} {'Coherence':<10} {'Half-Life (sec)':<15} {'Approx':<15}")
 print("-"*80)
 
 for Z, N, coh, hl in peaks[:20]:
    name = element_name(Z)
    if hl < 60:
        hl_str = f"{hl:.2f} s"
    elif hl < 86400:
        hl_str = f"{hl/60:.1f} min"
    else:
        hl_str = f"{hl/86400:.1f} days"
    print(f"{int(Z):<5} {int(N):<6} {name:<25} {coh:.4f} {hl:.2e} {hl_str}")
 # Dark matter mass spectrum
 print("\n" + "="*80)
 print("[v16] Dark Matter (T3 Branch) – Predicted Mass Spectrum from 27 Hz Anchor & 19:13 Ratio")
 print("="*80)
 f_c3 = anchor * (13.0/19.0) / 230.0
 h = 6.626e-34
 c = 3e8
 def freq_to_ev(f):
    return (h * f) / 1.602e-19 # joules to eV
 print(f"T3 cutoff frequency: {f_c3:.5f} Hz → mass ~ {freq_to_ev(f_c3):.2e} eV")
 for k in range(1, 8):
    f = k * f_c3
    m_ev = freq_to_ev(f)
    print(f" Harmonic {k}: {f:.5f} Hz → {m_ev:.2e} eV (dark particle mass candidate)")
 # Save to CSV
 df = pd.DataFrame(peaks, columns=['Z', 'N', 'Coherence', 'HalfLife_sec'])
 df['ElementName'] = df['Z'].apply(element_name)
 df.to_csv('/Users/4c/Desktop/GHQ/Tesla/RAD/anti_element_extended_v16.csv', index=False)
 print("\nTable saved to 'anti_element_extended_v16.csv'")
 fig_table, ax_txt = plt.subplots(figsize=(11, 7))
 ax_txt.axis('off')
 rows = []
 for Z, N, coh, hl in peaks[:12]:
    name = element_name(Z)
    if hl < 60:
        hl_str = f"{hl:.2f} s"
    elif hl < 86400:
        hl_str = f"{hl/60:.1f} min"
    else:
        hl_str = f"{hl/86400:.1f} days"
    rows.append(f"Z={int(Z):<3} N={int(N):<3} {name:<18} coh={coh:.4f}  half-life={hl_str}")
 table_text = "[v16] Extended Anti-Element Table (T2)\n" + "=" * 45 + "\n"
 table_text += "\n".join(rows) if rows else "Nema pikova za trenutne parametre."
 table_text += "\n\nCSV sacuvan: /Users/4c/Desktop/GHQ/Tesla/RAD/anti_element_extended_v16.csv"
 ax_txt.text(0.02, 0.98, table_text, va='top', family='monospace', fontsize=10)
 fig_table.tight_layout()
 fig_table.canvas.draw_idle()
 plt.figure(fig_table.number)
 plt.show(block=False)

table_btn.on_clicked(show_extended_table)

# =============================================================================
# BUTTON: QUANTUM HANDSHAKE T1–T2 (230th subharmonic)
# =============================================================================
ax_hs12 = plt.axes([0.48, 0.02, 0.18, 0.04])
hs12_btn = Button(ax_hs12, 'Handshake T1-T2', color='lightgray',
hovercolor='yellow')
def run_handshake_t1t2(event):
 cutoff = cutoff_slider.val
 fig_hs, ax_hs = plt.subplots(figsize=(8, 5))
 plt.subplots_adjust(bottom=0.2)
 ax_hs.set_xlim(0, 20)
 ax_hs.set_ylim(0, 1.2)
 ax_hs.set_xlabel('Time (s)')
 ax_hs.set_ylabel('Energy Extracted / Lock Status')
 ax_hs.set_title('[v16] Quantum Handshake T1↔T2 (230th subharmonic)\nEnergy Harvesting from Anti-Matter Branch')
 line_energy, = ax_hs.plot([], [], 'b-', label='Harvested Energy (scaled)')
 line_lock, = ax_hs.plot([], [], 'g--', label='Locked (1=yes)')
 ax_hs.legend(loc='upper left')
 hs = QuantumHandshakeT1T2(freq_hz=cutoff, phase_offset_deg=-1.0)
 t = np.linspace(0, 20, 2000)
 dt = t[1] - t[0]
 energy_log = []
 lock_log = []
 t2_phase = 0.0
 for ti in t:
    t2_phase = 0.5 * np.sin(2*np.pi*0.5*ti) + 0.2*ti
    hs.update(dt, t2_phase, coupling=0.5)
    energy_log.append(hs.energy_extracted)
    lock_log.append(1.0 if hs.locked else 0.0)
 line_energy.set_data(t, energy_log)
 line_lock.set_data(t, lock_log)
 ax_hs.relim()
 ax_hs.autoscale_view()
 fig_hs.show()
hs12_btn.on_clicked(run_handshake_t1t2)


# =============================================================================
# BUTTON: QUANTUM HANDSHAKE T1–T3 (dark resonance)
# =============================================================================
ax_hs13 = plt.axes([0.70, 0.02, 0.18, 0.04])
hs13_btn = Button(ax_hs13, 'Handshake T1-T3', color='lightgray',
hovercolor='yellow')
def run_handshake_t1t3(event):
 anchor = freq_slider.val
 dark_freq = anchor * (13.0/19.0) / 230.0
 fig_hs, ax_hs = plt.subplots(figsize=(8, 5))
 plt.subplots_adjust(bottom=0.2)
 ax_hs.set_xlim(0, 20)
 ax_hs.set_ylim(0, 1.2)
 ax_hs.set_xlabel('Time (s)')
 ax_hs.set_ylabel('Energy Extracted / Lock Status')
 ax_hs.set_title(f'[v16] Quantum Handshake T1↔T3 (Dark Resonance at {dark_freq:.5f} Hz)\nEnergy Harvesting from Dark Matter Background')
 line_energy, = ax_hs.plot([], [], 'b-', label='Harvested Energy (scaled)')
 line_lock, = ax_hs.plot([], [], 'g--', label='Locked (1=yes)')
 ax_hs.legend(loc='upper left')
 hs = QuantumHandshakeT1T3(freq_hz=dark_freq, phase_offset_deg=-2.0)
 t = np.linspace(0, 20, 2000)
 dt = t[1] - t[0]
 energy_log = []
 lock_log = []
 t3_phase = 0.0
 for ti in t:
    t3_phase = 0.3 * np.sin(2*np.pi*0.3*ti) + 0.1*ti
    hs.update(dt, t3_phase, coupling=0.3)
    energy_log.append(hs.energy_extracted)
    lock_log.append(1.0 if hs.locked else 0.0)
 line_energy.set_data(t, energy_log)
 line_lock.set_data(t, lock_log)
 ax_hs.relim()
 ax_hs.autoscale_view()
 fig_hs.show()

hs13_btn.on_clicked(run_handshake_t1t3)


# =============================================================================
# LOTO 7/39 – PREDIKCIJA NEXT (primena ideje koherencije na Srpski Loto)
# =============================================================================
# Ista ideja kao coherence_score, ali za loto broj b (1..39) na poziciji p.
# v16: loto predikcija cita klizace + dodaje backtest preko istorije.
LOTO_SEED = 39
LOTO_CSV = _Path(__file__).resolve().parents[2] / "data" / "loto7hh_4632_k47.csv"
LOTO_TXT = _Path(__file__).with_name("Tesla_predictiv_v16.txt")
LOTO_BACKTEST_TXT = _Path(__file__).with_name("Tesla_predictiv_v16_backtest.txt")
LOTO_BROJEVA = 7
LOTO_MNOZIOCI = (3, 6, 9, 12, 15, 18, 21)
LOTO_HARMONIJSKI = tuple(range(3, 40, 3))   # 3,6,9,...,39 -> "magic" skup za loto
LOTO_W_KOH = 0.6     # tezina koherencije
LOTO_W_FREQ = 0.4    # tezina realne pozicijske frekvencije
LOTO_K_SHRINK = 27   # stabilizacija frekvencije po poziciji
LOTO_EPS = 1e-9
TALAS_BAZA_CIKLUSA = 21
TALAS_GAIN = 0.35
TALAS_SIGMA_FOKUS = 0.16


def loto_ucitaj(csv_path=LOTO_CSV):
    """Ucitaj Num1..Num7 kao rastuce sortirane kombinacije."""
    redovi = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = _csv.DictReader(f)
        kolone = [f"Num{i}" for i in range(1, LOTO_BROJEVA + 1)]
        for row in reader:
            redovi.append([int(row[k]) for k in kolone])
    if not redovi:
        raise ValueError(f"CSV je prazan: {csv_path}")
    return np.array(redovi, dtype=int)


def loto_parametri_sa_klizaca():
    """Trenutni parametri za loto deo, direktno sa klizaca glavnog prozora."""
    return {
        "anchor": float(freq_slider.val),
        "ratio": float(ratio_slider.val),
        "cutoff": float(cutoff_slider.val),
        "n_exp": float(n_slider.val),
        "branch": float(branch_slider.val),
        "t3": float(t3_slider.val),
    }


def loto_koherencija(b, harmonik, pozicija, params):
    """Loto koherencija povezana sa klizacima iz Tesla_predictiv modela."""
    anchor = max(1.001, float(params["anchor"]))
    ratio = max(0.001, float(params["ratio"]))
    cutoff = float(params["cutoff"])
    n_exp = float(params["n_exp"])
    branch = float(params["branch"])
    t3 = float(params["t3"])

    faza = (b * harmonik) / anchor
    anchor_rez = np.exp(-5.0 * abs(faza - round(faza)))

    dist_h = min(abs(b - h) for h in LOTO_HARMONIJSKI)
    harm_bliz = np.exp(-dist_h / max(0.5, ratio * 2.0))

    cutoff_phase = (b + harmonik + pozicija + 1) * cutoff
    cutoff_rez = np.exp(-2.0 * abs(cutoff_phase - round(cutoff_phase)))

    n_val = np.log(b + 1.0) / np.log(anchor)
    if branch >= 0.5:
        n_target = n_exp
    elif branch <= -0.5:
        n_target = -n_exp
    else:
        n_target = n_exp * (13.0 / 19.0)
    n_rez = np.exp(-2.0 * abs(np.sin(np.pi * (n_val - n_target))))

    idealna_poz = harmonik / 3.0          # harmonik 3->poz1 ... 21->poz7
    poz_rez = np.exp(-0.5 * abs((pozicija + 1) - idealna_poz))

    branch_gain = 1.0
    if abs(branch) < 0.5:
        branch_gain = (1.0 - t3) + t3 * 0.8

    return float(np.clip(anchor_rez * harm_bliz * cutoff_rez * n_rez * poz_rez * branch_gain, 0.0, 1.0))


def _loto_norm(d):
    if not d:
        return {}
    v = np.array(list(d.values()), dtype=float)
    raspon = float(v.max() - v.min())
    if raspon <= 0:
        return {k: 0.0 for k in d}
    mn = float(v.min())
    return {k: (float(d[k]) - mn) / raspon for k in d}


def loto_shrink_frekvencija(pojave):
    """Dirichlet shrinkage: svaka pozicija dobija blag uniformni prior."""
    if not pojave:
        return {}
    alpha = LOTO_K_SHRINK / float(len(pojave))
    return {b: float(c) + alpha for b, c in pojave.items()}


def loto_rang(izvlacenja, pozicija, harmonik, params):
    """Rang kandidata za jednu poziciju: koherencija + shrink pozicijska frekvencija."""
    pojave = {}
    for red in izvlacenja:
        b = int(red[pozicija])
        pojave[b] = pojave.get(b, 0) + 1
    freq_shrink = loto_shrink_frekvencija(pojave)
    freq_n = _loto_norm(freq_shrink)
    koh = {b: loto_koherencija(b, harmonik, pozicija, params) for b in pojave}
    koh_n = _loto_norm(koh)
    rang = []
    for b in pojave:
        skor = (koh_n[b] + LOTO_EPS) ** LOTO_W_KOH * (freq_n[b] + LOTO_EPS) ** LOTO_W_FREQ
        rang.append({"broj": b, "skor": float(skor), "koh": float(koh[b]),
                     "hl": float(half_life_from_coherence(koh[b])), "pojave": int(pojave[b]),
                     "freq_shrink": float(freq_shrink[b])})
    return sorted(rang, key=lambda r: (r["skor"], r["pojave"], -r["broj"]), reverse=True)


def loto_predikcija(izvlacenja, params):
    """v16: globalno optimalno uparivanje 7 pozicija (madjarski algoritam).

    Umesto greedy izbora poziciju-po-poziciju, biramo 7 razlicitih brojeva tako da
    UKUPAN skor cele kombinacije bude maksimalan (linear_sum_assignment).
    """
    from scipy.optimize import linear_sum_assignment

    rangovi = [(m, loto_rang(izvlacenja, poz, m, params))
               for poz, m in enumerate(LOTO_MNOZIOCI)]

    skor_map = [{r["broj"]: r["skor"] for r in rang} for _, rang in rangovi]
    kandidati = sorted({b for d in skor_map for b in d})
    idx = {b: j for j, b in enumerate(kandidati)}

    # Cost = -skor (minimizacija daje maksimalan ukupan skor).
    cost = np.zeros((len(LOTO_MNOZIOCI), len(kandidati)))
    for i, d in enumerate(skor_map):
        for b, s in d.items():
            cost[i, idx[b]] = -s

    redovi, kolone = linear_sum_assignment(cost)
    dodela = {int(r): kandidati[int(c)] for r, c in zip(redovi, kolone)}

    rezultati, izabrani = [], []
    for poz, (m, rang) in enumerate(rangovi):
        broj = dodela[poz]
        izbor = next((r for r in rang if r["broj"] == broj),
                     {"broj": broj, "skor": skor_map[poz].get(broj, 0.0),
                      "koh": 0.0, "hl": 0.0, "pojave": 0, "freq_shrink": 0.0})
        izabrani.append(broj)
        rezultati.append({"pozicija": poz + 1, "harmonik": m, "izbor": izbor, "rang": rang})
    return rezultati, sorted(izabrani)


def loto_kbest_kombinacije(izvlacenja, params, koliko=3):
    """v16: top-N najboljih GLOBALNIH kombinacija (k-best assignment, Murty-lite).

    Trazi 'koliko' razlicitih uparivanja 7 pozicija sa najvecim ukupnim skorom.
    """
    from scipy.optimize import linear_sum_assignment
    import heapq

    rangovi = [(m, loto_rang(izvlacenja, poz, m, params))
               for poz, m in enumerate(LOTO_MNOZIOCI)]
    skor_map = [{r["broj"]: r["skor"] for r in rang} for _, rang in rangovi]
    kandidati = sorted({b for d in skor_map for b in d})
    idx = {b: j for j, b in enumerate(kandidati)}

    n_poz, n_kand = len(LOTO_MNOZIOCI), len(kandidati)
    base = np.zeros((n_poz, n_kand))
    for i, d in enumerate(skor_map):
        for b, s in d.items():
            base[i, idx[b]] = -s   # minimizacija

    VELIKO = 1e9

    def resi(zabranjeni):
        c = base.copy()
        for (i, j) in zabranjeni:
            c[i, j] = VELIKO
        r, k = linear_sum_assignment(c)
        ukupno = float(c[r, k].sum())
        return ukupno, tuple(zip(r.tolist(), k.tolist()))

    ukupno0, dod0 = resi(set())
    heap = [(ukupno0, dod0, frozenset())]
    vidjeni, rezultat = set(), []

    while heap and len(rezultat) < koliko:
        ukupno, dodela, zabr = heapq.heappop(heap)
        kljuc = tuple(sorted(c for _, c in dodela))
        if kljuc in vidjeni:
            continue
        vidjeni.add(kljuc)
        brojevi = sorted(kandidati[c] for _, c in dodela)
        rezultat.append({"ukupan_skor": -ukupno, "kombinacija": brojevi})
        for par in dodela:
            nova = set(zabr) | {par}
            try:
                u, d = resi(nova)
                if u < VELIKO / 2:
                    heapq.heappush(heap, (u, d, frozenset(nova)))
            except Exception:
                pass

    return rangovi, rezultat


def talas_sloj(mnozilac, nx):
    """Model B: jedan Tesla 3-6-9 talasni sloj (kao Tesla_369_7 logika)."""
    x = np.linspace(0.0, 1.0, nx)
    omotac = np.exp(-((x - 0.5) ** 2) / (2.0 * TALAS_SIGMA_FOKUS ** 2))
    s = TALAS_GAIN * omotac * np.sin(2.0 * np.pi * mnozilac * TALAS_BAZA_CIKLUSA * x)
    mx = np.max(np.abs(s))
    if mx > 0:
        s = s / mx
    e_x = -np.gradient(s, x[1] - x[0])
    return s, e_x


def talas_rang(izvlacenja, pozicija, harmonik):
    """Model B rang: shrink prosek talasne energije + shrink pozicijska frekvencija."""
    s, e_x = talas_sloj(harmonik, len(izvlacenja))
    energija = 0.5 * (s ** 2 + e_x ** 2)

    zbir, pojave = {}, {}
    for i, red in enumerate(izvlacenja):
        b = int(red[pozicija])
        zbir[b] = zbir.get(b, 0.0) + float(energija[i])
        pojave[b] = pojave.get(b, 0) + 1

    global_mean = float(np.mean(energija))
    talas = {
        b: (zbir[b] + LOTO_K_SHRINK * global_mean) / (pojave[b] + LOTO_K_SHRINK)
        for b in zbir
    }
    talas_n = _loto_norm(talas)
    freq_shrink = loto_shrink_frekvencija(pojave)
    freq_n = _loto_norm(freq_shrink)

    rang = []
    for b in talas:
        skor = (talas_n[b] + LOTO_EPS) ** LOTO_W_KOH * (freq_n[b] + LOTO_EPS) ** LOTO_W_FREQ
        rang.append({"broj": b, "skor": float(skor), "talas": float(talas_n[b]),
                     "pojave": int(pojave[b]), "freq_shrink": float(freq_shrink[b])})
    return sorted(rang, key=lambda r: (r["skor"], r["pojave"], -r["broj"]), reverse=True)


def talas_kombinacije(izvlacenja, koliko=3):
    """Model B: tri kombinacije po poziciji iz talasnog ranga."""
    rangovi = [(m, talas_rang(izvlacenja, poz, m))
               for poz, m in enumerate(LOTO_MNOZIOCI)]
    kombinacije = []
    for k in range(koliko):
        upotrebljeni, izbor_po_poz = set(), []
        for _, rang in rangovi:
            izbor = None
            cnt = 0
            for r in rang:
                if r["broj"] in upotrebljeni:
                    continue
                if cnt == k:
                    izbor = r["broj"]
                    break
                cnt += 1
            if izbor is None:
                for r in rang:
                    if r["broj"] not in upotrebljeni:
                        izbor = r["broj"]
                        break
            upotrebljeni.add(izbor)
            izbor_po_poz.append(izbor)
        kombinacije.append(sorted(izbor_po_poz))
    return rangovi, kombinacije


def loto_tekst_topn(rangovi, resenja, n, params, naslov):
    linije = [
        naslov,
        f"CSV: {LOTO_CSV}",
        f"Izvlacenja: {n} | Seed: {LOTO_SEED}",
        "Parametri sa klizaca: "
        f"anchor={params['anchor']:.3f} ratio={params['ratio']:.4f} "
        f"cutoff={params['cutoff']:.4f} n={params['n_exp']:.2f} "
        f"branch={params['branch']:.2f} t3={params['t3']:.2f}",
        f"Harmonici: {LOTO_MNOZIOCI} | tezine: koh={LOTO_W_KOH} freq={LOTO_W_FREQ} | K_SHRINK={LOTO_K_SHRINK}",
        "",
        "Rang po pozicijama (top 5):",
    ]
    for poz, (m, rang) in enumerate(rangovi):
        top5 = ", ".join(f"{x['broj']:02d}({x['skor']:.4f})" for x in rang[:5])
        linije.append(f"  poz {poz + 1} (harmonik {m:2d}) -> [top: {top5}]")

    linije += ["", "PREDIKCIJE (3 najbolje globalne kombinacije):"]
    for i, res in enumerate(resenja, start=1):
        komb = " ".join(f"{b:02d}" for b in res["kombinacija"])
        linije.append(f"  Kombinacija {i} (ukupan skor={res['ukupan_skor']:.4f}):  {komb}")
    linije.append("")
    return "\n".join(linije) + "\n"


def loto_tekst_ab(rangovi_a, resenja_a, rangovi_b, kombinacije_b, n, params, naslov):
    """Zajednicki v16 izlaz: Model A (koherencija) + Model B (talas)."""
    linije = [
        naslov,
        f"CSV: {LOTO_CSV}",
        f"Izvlacenja: {n} | Seed: {LOTO_SEED}",
        "Parametri sa klizaca (Model A): "
        f"anchor={params['anchor']:.3f} ratio={params['ratio']:.4f} "
        f"cutoff={params['cutoff']:.4f} n={params['n_exp']:.2f} "
        f"branch={params['branch']:.2f} t3={params['t3']:.2f}",
        f"Harmonici: {LOTO_MNOZIOCI} | K_SHRINK={LOTO_K_SHRINK}",
        "",
        "MODEL A - Koherencija / top-N globalno (3 kombinacije):",
    ]

    for i, res in enumerate(resenja_a, start=1):
        komb = " ".join(f"{b:02d}" for b in res["kombinacija"])
        linije.append(f"  A{i} (ukupan skor={res['ukupan_skor']:.4f}):  {komb}")

    linije += ["", "MODEL B - Talasna energija / po poziciji (3 kombinacije):"]
    for i, komb in enumerate(kombinacije_b, start=1):
        linije.append(f"  B{i}:  " + " ".join(f"{b:02d}" for b in komb))

    linije += ["", "Model A rang po pozicijama (top 5):"]
    for poz, (m, rang) in enumerate(rangovi_a):
        top5 = ", ".join(f"{x['broj']:02d}({x['skor']:.4f})" for x in rang[:5])
        linije.append(f"  A poz {poz + 1} (h {m:2d}) -> [top: {top5}]")

    linije += ["", "Model B rang po pozicijama (top 5):"]
    for poz, (m, rang) in enumerate(rangovi_b):
        top5 = ", ".join(f"{x['broj']:02d}({x['skor']:.4f})" for x in rang[:5])
        linije.append(f"  B poz {poz + 1} (h {m:2d}) -> [top: {top5}]")

    linije.append("")
    return "\n".join(linije) + "\n"


def loto_backtest(izvlacenja, params, prozor=250, min_train=200):
    """Rolling backtest: za svako staro izvlacenje predvidi iz prethodne istorije."""
    if len(izvlacenja) <= min_train + 1:
        raise ValueError("Nema dovoljno izvlacenja za backtest.")

    start = max(min_train, len(izvlacenja) - prozor)
    rezultati = []

    for i in range(start, len(izvlacenja)):
        train = izvlacenja[:i]
        stvarno = set(int(x) for x in izvlacenja[i])
        _, kombinacija = loto_predikcija(train, params)
        pogodaka = len(set(kombinacija) & stvarno)
        rezultati.append(
            {
                "kolo": i + 1,
                "pogodaka": pogodaka,
                "predikcija": kombinacija,
                "stvarno": sorted(stvarno),
            }
        )

    return rezultati


def loto_backtest_tekst(rezultati, params):
    pogodci = np.array([r["pogodaka"] for r in rezultati], dtype=int)
    linije = [
        "Tesla Predictiv v16 - BACKTEST Loto 7/39",
        f"Broj testiranih kola: {len(rezultati)}",
        "Parametri sa klizaca: "
        f"anchor={params['anchor']:.3f} ratio={params['ratio']:.4f} "
        f"cutoff={params['cutoff']:.4f} n={params['n_exp']:.2f} "
        f"branch={params['branch']:.2f} t3={params['t3']:.2f}",
        f"Prosek pogodaka: {float(np.mean(pogodci)):.4f}",
        f"Medijana pogodaka: {float(np.median(pogodci)):.2f}",
        f"Najbolji pogodak: {int(np.max(pogodci))}",
        "",
        "Raspodela pogodaka:",
    ]

    for k in range(0, 8):
        linije.append(f"  {k} pogodaka: {int(np.sum(pogodci == k))}")

    linije += ["", "Zadnjih 20 testiranih kola:"]
    for r in rezultati[-20:]:
        pred = " ".join(f"{b:02d}" for b in r["predikcija"])
        stvarno = " ".join(f"{b:02d}" for b in r["stvarno"])
        linije.append(f"  kolo {r['kolo']:4d}: pogodaka={r['pogodaka']}  pred={pred}  stvarno={stvarno}")

    return "\n".join(linije) + "\n"


# =============================================================================
# BUTTON: PREDIKCIJA NEXT (Loto 7/39)
# =============================================================================
ax_loto = plt.axes([0.01, 0.92, 0.18, 0.05])
loto_btn = Button(ax_loto, 'v16 Predikcija', color='lightgreen', hovercolor='lime')


LOTO_NASLOV = "Tesla Predictiv v16 - Loto 7/39 (A koherencija + B talas)"


def show_predikcija_next(event):
    np.random.seed(LOTO_SEED)
    params = loto_parametri_sa_klizaca()
    izvlacenja = loto_ucitaj()
    rangovi_a, resenja_a = loto_kbest_kombinacije(izvlacenja, params, koliko=3)
    rangovi_b, kombinacije_b = talas_kombinacije(izvlacenja, koliko=3)
    tekst = loto_tekst_ab(rangovi_a, resenja_a, rangovi_b, kombinacije_b,
                          len(izvlacenja), params, LOTO_NASLOV)
    LOTO_TXT.write_text(tekst, encoding="utf-8")
    print("\n" + tekst)
    print(f"Sacuvano: {LOTO_TXT}")

    fig_loto, ax_l = plt.subplots(figsize=(10, 7))
    ax_l.axis('off')
    prikaz = tekst + f"\nCSV/TXT: {LOTO_TXT}"
    ax_l.text(0.02, 0.98, prikaz, va='top', family='monospace', fontsize=10)
    fig_loto.tight_layout()
    fig_loto.canvas.draw_idle()
    fig_loto.show()


loto_btn.on_clicked(show_predikcija_next)


# =============================================================================
# BUTTON: BACKTEST (Loto 7/39)
# =============================================================================
ax_loto_bt = plt.axes([0.20, 0.92, 0.18, 0.05])
loto_bt_btn = Button(ax_loto_bt, 'v16 Backtest', color='lightblue', hovercolor='cyan')


def show_loto_backtest(event):
    np.random.seed(LOTO_SEED)
    params = loto_parametri_sa_klizaca()
    izvlacenja = loto_ucitaj()
    rezultati = loto_backtest(izvlacenja, params)
    tekst = loto_backtest_tekst(rezultati, params)
    LOTO_BACKTEST_TXT.write_text(tekst, encoding="utf-8")
    print("\n" + tekst)
    print(f"Backtest sacuvan: {LOTO_BACKTEST_TXT}")

    fig_bt, ax_bt = plt.subplots(figsize=(11, 7))
    ax_bt.axis('off')
    ax_bt.text(0.02, 0.98, tekst, va='top', family='monospace', fontsize=9)
    fig_bt.tight_layout()
    fig_bt.canvas.draw_idle()
    fig_bt.show()


loto_bt_btn.on_clicked(show_loto_backtest)


# Pri startu odmah generisi/osvezi Tesla_predictiv_v16.txt (ne ceka klik na dugme).
np.random.seed(LOTO_SEED)
_params = loto_parametri_sa_klizaca()
_izv = loto_ucitaj()
_rangovi_a, _resenja_a = loto_kbest_kombinacije(_izv, _params, koliko=3)
_rangovi_b, _kombinacije_b = talas_kombinacije(_izv, koliko=3)
LOTO_TXT.write_text(
    loto_tekst_ab(_rangovi_a, _resenja_a, _rangovi_b, _kombinacije_b,
                  len(_izv), _params, LOTO_NASLOV),
    encoding="utf-8",
)
print(f"Tesla_predictiv_v16.txt generisan pri startu: {LOTO_TXT}")


# =============================================================================
# LAUNCH INTERACTIVE WINDOW
# =============================================================================
plt.show()



"""
================================================================================
[v16] Extended Anti-Element Table (T2 Reverse Time Branch) – Coherence & Predicted Half-Life
================================================================================
Z     N      Element Name              Coherence  Half-Life (sec) Approx         
--------------------------------------------------------------------------------
142   318    Unquadbiium               0.0499 2.75e-03 0.00 s
140   320    Unquadnilium              0.0496 2.75e-03 0.00 s
182   278    Unoctbiium                0.0495 2.75e-03 0.00 s
138   322    Untrioctium               0.0493 2.75e-03 0.00 s
136   324    Untrihexium               0.0490 2.74e-03 0.00 s
134   326    Untriquadium              0.0487 2.74e-03 0.00 s
132   328    Untribiium                0.0484 2.73e-03 0.00 s
130   330    Untrinilium               0.0481 2.73e-03 0.00 s
128   332    Unbioctium                0.0478 2.73e-03 0.00 s
126   334    Unbihexium                0.0476 2.72e-03 0.00 s
144   316    Unquadquadium             0.0454 2.69e-03 0.00 s
180   280    Unoctnilium               0.0444 2.68e-03 0.00 s
124   336    Unbiquadium               0.0428 2.66e-03 0.00 s
146   314    Unquadhexium              0.0413 2.64e-03 0.00 s
178   282    Unseptoctium              0.0399 2.62e-03 0.00 s
122   338    Unbibiium                 0.0385 2.61e-03 0.00 s
148   312    Unquadoctium              0.0376 2.60e-03 0.00 s
176   284    Unsepthexium              0.0358 2.57e-03 0.00 s
120   340    Unbinilium                0.0346 2.56e-03 0.00 s
150   310    Unpentnilium              0.0343 2.56e-03 0.00 s

================================================================================
[v16] Dark Matter (T3 Branch) – Predicted Mass Spectrum from 27 Hz Anchor & 19:13 Ratio
================================================================================
T3 cutoff frequency: 0.08032 Hz → mass ~ 3.32e-16 eV
 Harmonic 1: 0.08032 Hz → 3.32e-16 eV (dark particle mass candidate)
 Harmonic 2: 0.16064 Hz → 6.64e-16 eV (dark particle mass candidate)
 Harmonic 3: 0.24096 Hz → 9.97e-16 eV (dark particle mass candidate)
 Harmonic 4: 0.32128 Hz → 1.33e-15 eV (dark particle mass candidate)
 Harmonic 5: 0.40160 Hz → 1.66e-15 eV (dark particle mass candidate)
 Harmonic 6: 0.48192 Hz → 1.99e-15 eV (dark particle mass candidate)
 Harmonic 7: 0.56224 Hz → 2.33e-15 eV (dark particle mass candidate)

Table saved to 'anti_element_extended_v16.csv'
/Tesla/RAD/Tesla_predictiv_v16.py:132: RuntimeWarning: overflow encountered in exp
  return np.exp(log_hl)

Tesla Predictiv v16 - Loto 7/39 (koherencija + 7 harmonika + klizaci)
CSV: /data/loto7hh_4632_k47.csv
Izvlacenja: 4632 | Seed: 39 | Anchor: 21
Harmonici: (3, 6, 9, 12, 15, 18, 21) | tezine: koh=0.6 freq=0.4

Predikcija po pozicijama:
  poz 1 (harmonik  3) -> 07  skor=0.536381  koh=0.7165  pojave=290  [top: 07(0.5364), 06(0.4348), 01(0.3605), 08(0.3020), 14(0.2916)]
  poz 2 (harmonik  6) ->  x  skor=0.597587  koh=0.7165  pojave=192  [top: 07(0.7562), 14(0.5976), 03(0.4699), 21(0.4435), 11(0.4414)]
  poz 3 (harmonik  9) -> 21  skor=0.803231  koh=1.0000  pojave=171  [top: 21(0.8032), 14(0.7909), 07(0.6447), 12(0.6108), 09(0.5540)]
  poz 4 (harmonik 12) -> 28  skor=0.599233  koh=0.7165  pojave=142  [top: 21(0.9944), 14(0.6742), 28(0.5992), 23(0.4770), 12(0.4743)]
  poz 5 (harmonik 15) ->  y  skor=0.599234  koh=0.4895  pojave=286  [top: 21(0.8983), 28(0.7791), 24(0.5992), 35(0.4777), 25(0.4534)]
  poz 6 (harmonik 18) ->  z  skor=0.785770  koh=0.7165  pojave=373  [top: 35(0.7858), 28(0.6973), 36(0.5348), 21(0.5031), 27(0.4851)]
  poz 7 (harmonik 21) -> 39  skor=1.000000  koh=1.0000  pojave=849  [top: 39(1.0000), 36(0.7843), 33(0.6251), 30(0.4781), 27(0.3467)]

FINALNA next kombinacija:
  07 x 21 y 28 z 39


Sacuvano: /Tesla/RAD/Tesla_predictiv_v16.txt
"""


"""
Razdvoji „talas" i „koherenciju" kao dva izbora. 
Možeš dodati prekidač: 
model A = koherencija (ovaj v16), 
model B = talasna energija (Tesla_369_7), 
pa uporediti koji istorijski bolje pogađa.
"""


"""
Dodato novo dugme v16 Backtest.
Backtest radi rolling proveru: za stara kola predviđa iz prethodne istorije i meri koliko brojeva bi pogodio.
U backtest TXT upisuje:
broj testiranih kola,
parametre sa klizača,
prosek pogodaka,
medijanu,
najbolji pogodak,
raspodelu 0–7 pogodaka,
zadnjih 20 testiranih kola.
"""




"""
source ~/tesla_env/bin/activate

Bitne verzije za tesla_env:

Paket	Verzija
python  3.11.13
numpy   2.2.6
scipy   1.15.3
pandas  3.0.3
matplotlib    3.10.9
k-Wave-python 0.6.2
pycharge      2.0.1
jax        0.10.1
jaxlib     0.10.1
jaxtyping  0.3.7
equinox    0.13.8
lineax     0.1.1
optimistix 0.1.0
ml-dtypes
(uz jax)
opencv-python 4.13.0.92
h5py          3.16.0
"""
