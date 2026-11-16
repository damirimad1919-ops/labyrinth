# -*- coding: utf-8 -*-
"""
СРО: «Кәсіпорынның өндірістік ресурстарын оңтайландыру арқылы пайданы
максимизациялаудың математикалық және компьютерлік моделі»

Компьютерлік модель:
  1) бастапқы деректерді енгізу;
  2) мақсаттық функция мен шектеулер жүйесін анықтау;
  3) SciPy (HiGHS) арқылы сызықтық бағдарламалау есебін шешу;
  4) өзіндік симплекс алгоритмімен қолмен есептеуді қайталап тексеру;
  5) ресурстардың пайдаланылуын, қалдықтарын, көлеңкелі бағаларын есептеу;
  6) бүтінсанды модельді (MILP) шешу;
  7) ресурстар 10% және 20% артқандағы сезімталдықты талдау;
  8) графиктер салу (figures/ қалтасына сақталады).

Іске қосу:  python optimization_model.py
Қажетті кітапханалар: numpy, scipy (>=1.9), matplotlib
"""
import os
from fractions import Fraction

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds
import matplotlib
matplotlib.use("Agg")                 # графиктерді экрансыз файлға сақтау
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "DejaVu Sans"   # қазақ әріптерін қолдайтын қаріп
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. БАСТАПҚЫ ДЕРЕКТЕР (шартты деректер)
#    x1 – А өнімінің апталық көлемі, x2 – В өнімінің апталық көлемі
#    (өлшем бірлігі – партия, 1 партия = 100 дана)
# ---------------------------------------------------------------------------
products = ["А өнімі (x1)", "В өнімі (x2)"]
resources = ["Шикізат, т", "Еңбек уақыты, жүз адам-сағ", "Жабдық, станок-сағ"]

c = np.array([300.0, 200.0])          # 1 партияның пайдасы, мың теңге
A = np.array([[2.0, 1.0],             # шикізат шығыны, т/партия
              [1.0, 1.0],             # еңбек шығыны, жүз адам-сағ/партия
              [1.0, 3.0]])            # жабдық уақыты, станок-сағ/партия
b = np.array([100.0, 80.0, 180.0])    # апталық ресурс қоры

x_base = np.array([20.0, 40.0])       # кәсіпорынның қазіргі (бастапқы) жоспары


# ---------------------------------------------------------------------------
# 2. ЖЗБ ЕСЕБІН ШЕШУ (SciPy linprog, HiGHS әдісі)
#    linprog минимумды іздейді, сондықтан max Z = c·x  <=>  min (-c)·x
# ---------------------------------------------------------------------------
def solve_lp(c, A, b):
    res = linprog(-c, A_ub=A, b_ub=b, bounds=[(0, None)] * len(c), method="highs")
    if not res.success:
        raise RuntimeError(res.message)
    x = res.x
    z = -res.fun
    used = A @ x                      # пайдаланылған ресурс
    slack = b - used                  # ресурс қалдығы
    shadow = -res.ineqlin.marginals   # көлеңкелі (қосарланған) бағалар y_i
    return x, z, used, slack, shadow


# ---------------------------------------------------------------------------
# 3. ӨЗІНДІК СИМПЛЕКС АЛГОРИТМІ (дәл бөлшектермен) – қолмен шешуді тексеру
# ---------------------------------------------------------------------------
def simplex_tableau(c, A, b, verbose=True):
    m, n = A.shape
    F = Fraction
    # Кесте: [x1..xn | s1..sm | b], соңғы жол – Z-жолы (Δj бағалары)
    T = [[F(int(A[i, j])) for j in range(n)] +
         [F(1 if k == i else 0) for k in range(m)] + [F(int(b[i]))] for i in range(m)]
    T.append([F(-int(cj)) for cj in c] + [F(0)] * m + [F(0)])
    basis = [n + i for i in range(m)]
    names = [f"x{j+1}" for j in range(n)] + [f"s{i+1}" for i in range(m)]

    def show(it):
        print(f"\n--- Симплекс кестесі, итерация {it} ---")
        print("Базис | " + " | ".join(f"{nm:>6}" for nm in names) + " |      b")
        for i in range(m):
            print(f"{names[basis[i]]:>5} | " + " | ".join(f"{str(v):>6}" for v in T[i][:-1])
                  + f" | {str(T[i][-1]):>6}")
        print(f"{'Z':>5} | " + " | ".join(f"{str(v):>6}" for v in T[m][:-1])
              + f" | {str(T[m][-1]):>6}")

    it = 0
    if verbose:
        show(it)
    while True:
        col = min(range(n + m), key=lambda j: T[m][j])
        if T[m][col] >= 0:            # оптималдық шарты: барлық Δj >= 0
            break
        ratios = [(T[i][-1] / T[i][col], i) for i in range(m) if T[i][col] > 0]
        if not ratios:
            raise RuntimeError("Мақсаттық функция шектелмеген")
        _, row = min(ratios)
        piv = T[row][col]
        if verbose:
            print(f"Енгізілетін айнымалы: {names[col]}, шығарылатын: {names[basis[row]]}, "
                  f"тірек элементі = {piv}")
        T[row] = [v / piv for v in T[row]]
        for i in range(m + 1):
            if i != row and T[i][col] != 0:
                k = T[i][col]
                T[i] = [vi - k * vr for vi, vr in zip(T[i], T[row])]
        basis[row] = col
        it += 1
        if verbose:
            show(it)
    sol = [F(0)] * (n + m)
    for i in range(m):
        sol[basis[i]] = T[i][-1]
    return sol, T[m][-1], T[m][n:n + m]


# ---------------------------------------------------------------------------
# 4. БҮТІНСАНДЫ МОДЕЛЬ (MILP)
# ---------------------------------------------------------------------------
def solve_milp(c, A, b):
    res = milp(-c, constraints=LinearConstraint(A, -np.inf, b),
               integrality=np.ones(len(c)), bounds=Bounds(0, np.inf))
    return res.x, -res.fun


def report(title, x, z, used, slack, shadow, b):
    print(f"\n===== {title} =====")
    print(f"x1 = {x[0]:.4f},  x2 = {x[1]:.4f},  Z_max = {z:.2f} мың теңге")
    for i, r in enumerate(resources):
        status = "ШЕКТЕУШІ (тапшы)" if abs(slack[i]) < 1e-9 else "артық қалдық бар"
        print(f"  {r:<28} пайдаланылды {used[i]:8.2f} / {b[i]:7.2f} "
              f"({100 * used[i] / b[i]:6.2f}%), қалдық {slack[i]:6.2f}, "
              f"y = {shadow[i]:7.2f}  -> {status}")


if __name__ == "__main__":
    # ---- 4.1 Негізгі есеп ----
    x, z, used, slack, shadow = solve_lp(c, A, b)
    report("ОҢТАЙЛЫ ШЕШІМ (SciPy / HiGHS)", x, z, used, slack, shadow, b)

    # ---- 4.2 Симплекс әдісімен тексеру ----
    sol, z_s, y_s = simplex_tableau(c, A, b)
    print("\nСимплекс нәтижесі:", {f"x{j+1}": str(sol[j]) for j in range(2)},
          "s:", [str(v) for v in sol[2:]], "Z =", z_s, "y =", [str(v) for v in y_s])
    assert np.allclose([float(v) for v in sol[:2]], x) and abs(float(z_s) - z) < 1e-9

    # ---- 4.3 Қосарланған есеп арқылы тексеру: W = b·y = Z ----
    print(f"\nҚосарланған мақсат W = b·y = {b @ shadow:.2f} (Z = {z:.2f})")

    # ---- 4.4 Бастапқы жоспармен салыстыру ----
    z_base = c @ x_base
    print(f"\nБастапқы жоспар x = {x_base}, Z = {z_base:.0f}; ресурс шығыны {A @ x_base}")
    print(f"Пайда өсімі: {z - z_base:.0f} мың тг ({100 * (z - z_base) / z_base:.2f}%)")

    # ---- 4.5 Сезімталдық талдауы ----
    scenarios = {"Базалық": b.copy()}
    for p in (0.10, 0.20):
        for i, short in enumerate(["Шикізат", "Еңбек", "Жабдық"]):
            bb = b.copy(); bb[i] *= 1 + p
            scenarios[f"{short} +{int(p*100)}%"] = bb
        scenarios[f"Барлық ресурс +{int(p*100)}%"] = b * (1 + p)

    print("\n===== СЕЗІМТАЛДЫҚ ТАЛДАУЫ =====")
    print(f"{'Сценарий':<22}{'x1':>8}{'x2':>8}{'Z (ЖЗБ)':>10}{'ΔZ,%':>8}"
          f"{'x1*':>6}{'x2*':>6}{'Z (бүтін)':>11}  Тапшы ресурстар")
    sens = {}
    for name, bb in scenarios.items():
        xs, zs, us, ss, ys = solve_lp(c, A, bb)
        xi, zi = solve_milp(c, A, bb)
        binding = ", ".join(r.split(",")[0] for r, s in zip(resources, ss) if abs(s) < 1e-7)
        sens[name] = (xs, zs, zi)
        print(f"{name:<22}{xs[0]:8.2f}{xs[1]:8.2f}{zs:10.1f}{100*(zs-z)/z:8.2f}"
              f"{xi[0]:6.0f}{xi[1]:6.0f}{zi:11.0f}  {binding}")

    # ---- 4.6 Көлеңкелі бағаның тұрақтылық аралықтары (параметрлік талдау) ----
    print("\n===== b_i ӨЗГЕРГЕНДЕГІ Z(b_i) (параметрлік талдау) =====")
    grid = np.linspace(0.5, 1.6, 111)
    param = {}
    for i in range(3):
        zs = []
        for k in grid:
            bb = b.copy(); bb[i] = b[i] * k
            zs.append(solve_lp(c, A, bb)[1])
        param[i] = np.array(zs)

    # =======================================================================
    # 5. ГРАФИКТЕР
    # =======================================================================
    # 5.1 Мүмкін шешімдер облысы және изопайда сызықтары
    fig, ax = plt.subplots(figsize=(8, 6.5))
    x1 = np.linspace(0, 70, 500)
    lines = [(100 - 2 * x1), (80 - x1), (180 - x1) / 3]
    colors = ["#1f77b4", "#2ca02c", "#d62728"]
    labels = ["Шикізат: 2x1 + x2 ≤ 100", "Еңбек: x1 + x2 ≤ 80", "Жабдық: x1 + 3x2 ≤ 180"]
    for y, col, lab in zip(lines, colors, labels):
        ax.plot(x1, y, color=col, lw=2, label=lab)
    upper = np.minimum.reduce(lines)
    ax.fill_between(x1, 0, np.clip(upper, 0, None), where=upper >= 0,
                    color="#ffcc66", alpha=0.45, label="Мүмкін шешімдер облысы")
    for zl, ls in [(12000, ":"), (15000, "--"), (z, "-")]:
        ax.plot(x1, (zl - 300 * x1) / 200, "k", ls=ls, lw=1.2,
                label=f"Изопайда Z = {zl:.0f}")
    verts = np.array([[0, 0], [50, 0], [24, 52], [0, 60]])
    ax.scatter(verts[:, 0], verts[:, 1], color="k", zorder=5)
    for vx, vy in verts:
        ax.annotate(f"({vx:.0f}; {vy:.0f})", (vx, vy), textcoords="offset points",
                    xytext=(6, 6))
    ax.scatter([x[0]], [x[1]], s=160, color="red", zorder=6, marker="*",
               label=f"Оптимум ({x[0]:.0f}; {x[1]:.0f}), Z = {z:.0f}")
    ax.scatter(*x_base, s=70, color="purple", marker="s", zorder=6,
               label=f"Бастапқы жоспар (20; 40), Z = {z_base:.0f}")
    ax.annotate("", xy=(24 + 9, 52 + 6), xytext=(24, 52),
                arrowprops=dict(arrowstyle="->", color="k"))
    ax.set_xlim(0, 70); ax.set_ylim(0, 90)
    ax.set_xlabel("x1 – А өнімі, партия/апта"); ax.set_ylabel("x2 – В өнімі, партия/апта")
    ax.set_title("1-сурет. Есептің графиктік шешімі")
    ax.legend(fontsize=8, loc="upper right"); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "fig1_feasible_region.png"), dpi=200)
    plt.close(fig)

    # 5.2 Ресурстарды пайдалану (оптимум және бастапқы жоспар)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    idx = np.arange(3); w = 0.35
    pct_opt = 100 * used / b; pct_base = 100 * (A @ x_base) / b
    b1 = ax.bar(idx - w / 2, pct_base, w, color="#9e9ac8", label="Бастапқы жоспар")
    b2 = ax.bar(idx + w / 2, pct_opt, w, color="#3182bd", label="Оңтайлы жоспар")
    ax.bar_label(b1, fmt="%.1f%%", fontsize=9); ax.bar_label(b2, fmt="%.1f%%", fontsize=9)
    ax.axhline(100, color="r", ls="--", lw=1)
    ax.set_xticks(idx, ["Шикізат", "Еңбек уақыты", "Жабдық"])
    ax.set_ylabel("Ресурсты пайдалану, %"); ax.set_ylim(0, 115)
    ax.set_title("2-сурет. Ресурстардың пайдаланылу деңгейі")
    ax.legend(loc="lower right"); fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig2_resource_usage.png"), dpi=200); plt.close(fig)

    # 5.3 Сезімталдық: сценарийлер бойынша пайда
    fig, ax = plt.subplots(figsize=(9, 4.8))
    names = list(sens.keys()); vals = [sens[n][1] for n in names]
    colrs = ["#636363"] + ["#6baed6"] * 4 + ["#08519c"] * 4
    bars = ax.barh(names, vals, color=colrs)
    ax.bar_label(bars, fmt="%.0f", fontsize=9, padding=3)
    ax.axvline(z, color="r", ls="--", lw=1)
    ax.invert_yaxis(); ax.set_xlim(15000, 22500)
    ax.set_xlabel("Максималды пайда Z, мың теңге/апта")
    ax.set_title("3-сурет. Ресурстар 10% және 20% артқандағы пайда")
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "fig3_sensitivity.png"), dpi=200)
    plt.close(fig)

    # 5.4 Параметрлік талдау Z(b_i)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for i, col in enumerate(colors):
        ax.plot(grid * 100, param[i], color=col, lw=2, label=resources[i].split(",")[0])
    ax.axvline(100, color="gray", ls=":")
    ax.set_xlabel("Ресурс қорының базалық деңгейге қатысы, %")
    ax.set_ylabel("Z_max, мың теңге/апта")
    ax.set_title("4-сурет. Бір ресурс қоры өзгергендегі максималды пайда")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "fig4_parametric.png"), dpi=200); plt.close(fig)

    print(f"\nГрафиктер сақталды: {FIG_DIR}")
