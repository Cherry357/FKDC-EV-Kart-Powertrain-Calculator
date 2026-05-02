import streamlit as st
import math

# Page Config
st.set_page_config(page_title="FKDC Calculation Dashboard", layout="wide")

# Corrected CSS with the proper Streamlit argument
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stSlider, .stNumberInput { background-color: #1e293b; border-radius: 10px; padding: 10px; }
    h2 { color: #10b981 !important; border-bottom: 1px solid #334155; padding-top: 20px; }
    h3 { color: #f59e0b !important; }
    div[data-testid="stMetricValue"] { color: #ffffff; font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️ FKDC Calculation Dashboard")

# --- 1. USER INPUTS (Left Column & Middle) ---
col_in1, col_in2 = st.columns(2)

with col_in1:
    st.header("Kart Dynamics")
    # Verified against Screenshot 2026-05-02 182925.png
    mass = st.slider("Total Mass (kg)", 50.0, 300.0, 150.000, step=0.001, format="%.3f")
    top_speed_kmh = st.slider("Top Speed (km/h)", 10.0, 150.0, 80.000, step=0.001, format="%.3f")
    tire_radius = st.slider("Tire Radius (m)", 0.050, 0.300, 0.139, step=0.001, format="%.3f")
    crr = st.slider("Rolling Res. (Crr)", 0.005, 0.050, 0.015, step=0.001, format="%.3f")
    cd = st.slider("Aero Drag (Cd)", 0.100, 1.200, 0.800, step=0.001, format="%.3f")
    frontal_area = st.slider("Frontal Area (m²)", 0.100, 2.000, 0.600, step=0.001, format="%.3f")
    rho = st.slider("Air Density (ρ)", 1.000, 1.500, 1.225, step=0.001, format="%.3f")

with col_in2:
    st.header("Powertrain")
    # Verified against Screenshot 2026-05-02 183014.png
    motor_rpm_max = st.slider("Max Motor RPM", 1000, 12000, 4000, step=10)
    z1 = st.slider("Motor Sprocket (Z1)", 8, 30, 11, step=1)
    d_eff = st.slider("Drivetrain Eff. (%)", 50, 100, 85, step=1) / 100.0
    peak_amps = st.slider("Peak Limit (Amps)", 10, 500, 130, step=1)
    cont_amps = st.slider("Continuous (Amps)", 10, 300, 85, step=1)
    kt_constant = st.number_input("Motor Torque Constant (Nm/A)", 0.010, 2.000, 0.450, step=0.001, format="%.3f")

st.header("Battery Pack Architecture")
# Verified against Screenshot 2026-05-02 183030.png
b1, b2, b3 = st.columns(3)
with b1:
    S = st.number_input("Series Count (S)", 1, 120, 20)
    P = st.number_input("Parallel Count (P)", 1, 100, 16)
with b2:
    v_cell = st.number_input("Cell Nominal (V)", 1.0, 5.0, 3.600, format="%.3f")
    ah_cell = st.number_input("Cell Capacity (Ah)", 0.1, 20.0, 5.000, format="%.3f")
with b3:
    ir_cell = st.number_input("Cell IR (mΩ)", 1.0, 200.0, 30.000, format="%.3f")
    max_a_cell = st.number_input("Cell Max Rating (A)", 1.0, 100.0, 15.000, format="%.3f")

# --- 2. DYNAMIC CALCULATIONS ---
# Physics
g = 9.807
v_ms = top_speed_kmh / 3.6
tire_dia = tire_radius * 2

# Force/Power Calculations
f_roll = crr * mass * g
f_aero = 0.5 * rho * cd * frontal_area * (v_ms**2)
p_mech = (f_roll + f_aero) * v_ms
p_elec = p_mech / d_eff

# Transmission
# Gear Ratio = (RPM * PI * Dia) / (60 * V_ms)
gear_ratio = (motor_rpm_max * math.pi * tire_dia) / (60 * v_ms)
z2 = z1 * gear_ratio

# RAPDASA / Battery Physics
sys_v = S * v_cell
total_ah = P * ah_cell
total_cells = S * P
pack_res = (S * (ir_cell / 1000.0)) / P
v_sag = peak_amps * pack_res
v_at_load = sys_v - v_sag
amps_per_cell = peak_amps / P
c_rating = peak_amps / total_ah
cruising_amps = p_elec / sys_v
peak_torque_motor = peak_amps * kt_constant
peak_torque_axle = peak_torque_motor * gear_ratio * d_eff

# --- 3. DYNAMIC OUTPUTS ---
st.divider()
out_col1, out_col2 = st.columns(2)

with out_col1:
    st.header("Calculated Battery Architecture (RAPDASA)")
    # Verified against Screenshot 2026-05-02 183048.png
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SYSTEM VOLTAGE", f"{sys_v:.3f} V")
    m2.metric("TOTAL PACK AH", f"{total_ah:.3f} Ah")
    m3.metric("TOTAL CELL COUNT", f"{total_cells} Cells")
    m4.metric("PACK RESISTANCE", f"{(pack_res*1000):.3f} mΩ")

    st.write(f"Thermal Load (Peak): **{amps_per_cell:.3f} A / cell**")
    t_pct = min(amps_per_cell / max_a_cell, 1.0)
    st.progress(t_pct)
    st.caption("Safe" if t_pct < 1.0 else "⚠️ OVER CELL RATING")

    st.write(f"Voltage Sag: **{v_at_load:.3f} V (Drops {v_sag:.3f}V)**")
    st.progress(min(v_at_load / sys_v, 1.0))

with out_col2:
    st.header("Kinematics & Forces (Locked Output)")
    # VERBATIM requirements: Rolling Resistance, Aero Drag, Peak Current, Torque, Max RPM, Power...
    st.write(f"Rolling Resistance: **{f_roll:.3f} N**")
    st.write(f"Aerodynamic Drag: **{f_aero:.3f} N**")
    st.write(f"Peak Current: **{peak_amps:.3f} A**")
    st.write(f"Peak Torque (Axle): **{peak_torque_axle:.3f} Nm**")
    st.write(f"Max Motor RPM: **{motor_rpm_max} RPM**")
    st.write(f"Cruising Mech Power: **{(p_mech/1000):.3f} kW**")
    st.write(f"Cruising Elec Power: **{(p_elec/1000):.3f} kW**")
    st.write(f"Cruising Amp Draw: **{cruising_amps:.3f} A**")
    st.write(f"Estimated C-Rating: **{c_rating:.3f} C**")

    st.subheader("Motor RPM Matrix")
    st.write(f"Required Gear Ratio: **{gear_ratio:.3f} : 1**")
    st.write(f"Axle Sprocket (Z2): **{round(z2, 3)}** (Approx {round(z2)} teeth)")
    st.write(f"Tire Diameter: **{tire_dia:.3f} m**")

# --- 4. FORMULAS MAP ---
st.divider()
st.header("Engineering Formulas Map")
# Verified against Screenshot 2026-05-02 183125.png
f1, f2 = st.columns(2)
with f1:
    st.latex(r"F_{roll} = C_{rr} \times Mass \times g")
    st.latex(r"F_{aero} = 0.5 \times \rho \times C_d \times Area \times v^2")
    st.latex(r"P_{mech} = (F_{roll} + F_{aero}) \times v")
    st.latex(r"Torque_{axle} = (Peak\_Amps \times K_t) \times GR \times \eta")
with f2:
    st.latex(r"Pack Resistance = \frac{S \times Cell\_IR}{P}")
    st.latex(r"Voltage Sag = Peak\_Amps \times Pack\_Res")
    st.latex(r"Gear Ratio = \frac{N_{rpm} \times \pi \times Diameter}{60 \times v_{m/s}}")
    st.latex(r"C\_Rating = \frac{Peak\_Amps}{Total\_Ah}")