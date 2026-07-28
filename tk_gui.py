import tkinter as tk
from tkinter import ttk, messagebox
from simulator import NuclearPlant
import threading
import time

class NuclearPlantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Usina Nuclear")
        self.root.state('zoomed') # Maximizar janela ao iniciar
        
        # Instancia a planta nuclear (Backend)
        self.plant = NuclearPlant()
        self.plant.run_simulation = True
        self.trip_alert_shown = False # Flag para controlar o popup e não abrir vários ao mesmo tempo
        
        # Histórico para Gráficos (Listas que guardam os últimos valores)
        self.graph_history_pwr = []
        self.graph_history_tavg = []
        self.graph_history_press = []
        
        # Menu Bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Sair", command=root.quit)
        
        # Menu Falhas (Treinamento)
        # Aqui o instrutor pode inserir falhas para testar o operador
        failures_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inserir Falhas", menu=failures_menu)
        
        self.fail_spray_var = tk.BooleanVar()
        failures_menu.add_checkbutton(label="Spray Travado Aberto", onvalue=True, offvalue=False, variable=self.fail_spray_var, command=self.update_failures)
        
        self.fail_heaters_var = tk.BooleanVar()
        failures_menu.add_checkbutton(label="Falha nos Aquecedores", onvalue=True, offvalue=False, variable=self.fail_heaters_var, command=self.update_failures)
        
        self.fail_rods_var = tk.BooleanVar()
        failures_menu.add_checkbutton(label="Barras de Controle Travadas", onvalue=True, offvalue=False, variable=self.fail_rods_var, command=self.update_failures)
        
        self.fail_leak_var = tk.BooleanVar()
        failures_menu.add_checkbutton(label="Vazamento RCS (LOCA)", onvalue=True, offvalue=False, variable=self.fail_leak_var, command=self.update_failures)
        
        # Estilos (Tkinter Styling)
        style = ttk.Style()
        style.configure("TLabel", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 10))
        
        # --- Painel de Gráficos (Integrado - TOPO) ---
        # Canvas customizado para desenhar os gráficos em tempo real
        self.graphs_frame = ttk.LabelFrame(root, text="Gráficos em Tempo Real", padding="5")
        self.graphs_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.graphs_frame, bg="black", height=200)
        self.canvas.pack(fill="both", expand=True)
        
        # --- Container Principal (Dividir Tela) ---
        main_container = ttk.Frame(root)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        left_col = ttk.Frame(main_container)
        left_col.pack(side="left", fill="both", expand=True, padx=5)
        
        right_col = ttk.Frame(main_container)
        right_col.pack(side="right", fill="both", expand=True, padx=5)

        # --- Painel de Status (Esquerda) ---
        self.status_frame = ttk.LabelFrame(left_col, text="Status do Reator", padding="10")
        self.status_frame.pack(fill="x", pady=5)
        
        self.lbl_status = ttk.Label(self.status_frame, text="STATUS: NORMAL", foreground="green", font=("Helvetica", 14, "bold"))
        self.lbl_status.pack()
        
        # --- Painel de Variáveis (Esquerda) ---
        self.vars_frame = ttk.LabelFrame(left_col, text="Parâmetros Operacionais", padding="10")
        self.vars_frame.pack(fill="both", expand=True, pady=5)
        
        # Grid de variáveis (Mostradores Digitais)
        self.create_var_display(self.vars_frame, "Potência do Reator (%)", "rx_power_var", 0, 0)
        self.create_var_display(self.vars_frame, "Pressão do Pressurizador (Kg/cm²)", "prz_pressure_var", 1, 0)
        self.create_var_display(self.vars_frame, "Nível do Pressurizador (%)", "prz_level_var", 2, 0)
        self.create_var_display(self.vars_frame, "Temp. Média RCS (°C)", "rcs_temp_var", 3, 0)
        self.create_var_display(self.vars_frame, "Temp. Referência Tref (°C)", "tref_var", 3, 2) # Novo Display
        self.create_var_display(self.vars_frame, "Concentração de Boro (ppm)", "boron_var", 4, 0)
        self.create_var_display(self.vars_frame, "Nível do VCT (%)", "vct_level_var", 5, 0)
        self.create_var_display(self.vars_frame, "Potência Elétrica (MW)", "mw_var", 0, 2)
        self.create_var_display(self.vars_frame, "Pressão de Vapor (Kg/cm²)", "steam_pressure_var", 1, 2)
        self.create_var_display(self.vars_frame, "Carga da Turbina (%)", "turbine_load_var", 2, 2)
        
        # Advisor (Sistema de Avisos Inteligente)
        # Dá dicas ao operador baseado no estado atual da planta
        self.advisor_var = tk.StringVar()
        self.advisor_var.set("SISTEMA: Inicializando...")
        self.lbl_advisor = ttk.Label(self.vars_frame, textvariable=self.advisor_var, foreground="purple", font=("Helvetica", 11, "bold"))
        self.lbl_advisor.grid(row=6, column=0, columnspan=4, pady=10)
        
        # --- Painel de Controle (Direita) ---
        self.control_frame = ttk.LabelFrame(right_col, text="Controles do Operador", padding="10")
        self.control_frame.pack(fill="both", expand=True, pady=5)
        
        # Controle de Barras (Botões e Visualização)
        rods_frame = ttk.LabelFrame(self.control_frame, text="Barras de Controle", padding="5")
        rods_frame.pack(fill="x", pady=5)
        
        # Header com Toggle Auto/Manual
        rods_header = ttk.Frame(rods_frame)
        rods_header.pack(fill="x")
        ttk.Label(rods_header, text="Posição Atual:", font=("Helvetica", 10)).pack(side="left")
        
        self.auto_rods_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(rods_header, text="MODO AUTOMÁTICO", variable=self.auto_rods_var, command=self.toggle_auto_rods).pack(side="right")
        
        # Display Visual da Posição
        self.rods_display_var = tk.StringVar(value="100.0%")
        ttk.Label(rods_frame, textvariable=self.rods_display_var, font=("Consolas", 20, "bold"), foreground="darkblue").pack(anchor="center", pady=5)
        
        # Barra de Progresso Visual
        self.rods_progress = ttk.Progressbar(rods_frame, orient="horizontal", length=400, mode="determinate", maximum=100)
        self.rods_progress.pack(fill="x", padx=20, pady=5)
        
        # Botões de Movimento
        btn_frame = ttk.Frame(rods_frame)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="<< INSERIR (Dim. Potência)", command=lambda: self.move_rods(-5)).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="< INSERIR (Fino)", command=lambda: self.move_rods(-0.5)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="RETIRAR (Fino) >", command=lambda: self.move_rods(0.5)).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="RETIRAR (Aum. Potência) >>", command=lambda: self.move_rods(5)).grid(row=0, column=3, padx=5)
        
        # Controles CVCS (Boro)
        cvcs_frame = ttk.LabelFrame(self.control_frame, text="Sistema CVCS (Boro)", padding="5")
        cvcs_frame.pack(fill="x", pady=5)
        ttk.Button(cvcs_frame, text="BORAR (Add Boro)", command=lambda: self.plant.borate(10)).pack(side="left", expand=True, padx=2)
        ttk.Button(cvcs_frame, text="DILUIR (Add Água)", command=lambda: self.plant.dilute(10)).pack(side="left", expand=True, padx=2)
        
        # Controles Turbina
        turb_frame = ttk.LabelFrame(self.control_frame, text="Controle de Turbina (Carga)", padding="5")
        turb_frame.pack(fill="x", pady=5)
        
        # Header com Display da Carga
        turb_header = ttk.Frame(turb_frame)
        turb_header.pack(fill="x", pady=2)
        ttk.Label(turb_header, text="Carga Alvo:", font=("Helvetica", 10)).pack(side="left")
        ttk.Label(turb_header, textvariable=self.turbine_load_var, font=("Consolas", 12, "bold"), foreground="blue").pack(side="left", padx=5)

        # Botões de Carga
        btn_turb_frame = ttk.Frame(turb_frame)
        btn_turb_frame.pack(fill="x", pady=2)
        
        ttk.Button(btn_turb_frame, text="<< REDUZIR CARGA (-10%)", command=lambda: self.change_load(-10)).pack(side="left", expand=True, padx=2)
        ttk.Button(btn_turb_frame, text="< REDUZIR (-1%)", command=lambda: self.change_load(-1)).pack(side="left", expand=True, padx=2)
        ttk.Button(btn_turb_frame, text="AUMENTAR (+1%) >", command=lambda: self.change_load(1)).pack(side="left", expand=True, padx=2)
        ttk.Button(btn_turb_frame, text="AUMENTAR CARGA (+10%) >>", command=lambda: self.change_load(10)).pack(side="left", expand=True, padx=2)
        
        # Frame para Botões Laterais (Reset e Trip)
        buttons_frame = ttk.Frame(self.control_frame)
        buttons_frame.pack(fill="x", pady=10)
        
        # Botão de Salvar (Esquerda)
        self.btn_save = ttk.Button(buttons_frame, text="SALVAR LOGS", command=self.save_simulation_action)
        self.btn_save.pack(side="left", padx=5, expand=True, fill="x")

        # Botão de Reset (Centro)
        self.btn_reset = ttk.Button(buttons_frame, text="REINICIAR", command=self.restart_simulation_action)
        self.btn_reset.pack(side="left", padx=5, expand=True, fill="x")
        
        # Botão de Trip Manual (Direita)
        self.btn_trip = ttk.Button(buttons_frame, text="TRIP MANUAL", command=self.manual_trip)
        self.btn_trip.pack(side="left", padx=5, expand=True, fill="x")
        
        # Iniciar loop de atualização da GUI
        self.update_gui()
        self.update_graphs_loop()
        
        # Iniciar thread de simulação física (para não travar a GUI)
        # Usamos uma thread separada para que o cálculo matemático não congele a interface gráfica
        self.sim_thread = threading.Thread(target=self.run_simulation_loop, daemon=True)
        self.sim_thread.start()

    def create_var_display(self, parent, label_text, var_name, row, col):
        ttk.Label(parent, text=label_text).grid(row=row, column=col, sticky="w", padx=5, pady=2)
        setattr(self, var_name, tk.StringVar())
        ttk.Label(parent, textvariable=getattr(self, var_name), font=("Consolas", 12)).grid(row=row, column=col+1, sticky="e", padx=5, pady=2)

    def toggle_auto_rods(self):
        self.plant.auto_rods = self.auto_rods_var.get()

    def move_rods(self, delta):
        """ Move as barras de controle por um delta (positivo ou negativo) """
        self.plant.move_control_rods(delta)
        # Atualiza visualização imediata
        self.rods_display_var.set(f"{self.plant.rods_position:.1f}%")
        self.rods_progress['value'] = self.plant.rods_position

    def change_load(self, delta):
        """ Altera a carga da turbina """
        new_load = self.plant.turbine_load + delta
        self.plant.set_turbine_load(new_load)

    def manual_trip(self):
        self.plant.trigger_trip(["Manual Operator Action"])

    def save_simulation_action(self):
        """ Salva a simulação atual no banco de dados """
        self.plant.save_current_session()
        messagebox.showinfo("Salvo", "Dados da simulação salvos no banco de dados com sucesso!")

    def restart_simulation_action(self):
        """ Reinicia a simulação """
        if messagebox.askyesno("Confirmar Reinício", "Tem certeza que deseja reiniciar? Dados não salvos serão perdidos."):
            self.plant.run_simulation = True # Garantir que a flag está ativa
            self.plant.reset()
            
            # Verificar se a thread de simulação ainda está viva e reiniciar se necessário
            if not self.sim_thread.is_alive():
                print("Reiniciando thread de simulação...")
                self.sim_thread = threading.Thread(target=self.run_simulation_loop, daemon=True)
                self.sim_thread.start()

            self.trip_alert_shown = False
            self.rods_display_var.set(f"{self.plant.rods_position:.1f}%")
            self.rods_progress['value'] = self.plant.rods_position
            self.auto_rods_var.set(False) # Resetar toggle da GUI também
            
            # Resetar Menu de Falhas
            self.fail_spray_var.set(False)
            self.fail_heaters_var.set(False)
            self.fail_rods_var.set(False)
            self.fail_leak_var.set(False)
            
            messagebox.showinfo("RESET", "Simulação Reiniciada com Sucesso!")

    def update_failures(self):
        # Usando o novo método set_failure para garantir o log
        self.plant.set_failure("spray_stuck_open", self.fail_spray_var.get())
        self.plant.set_failure("heaters_fail", self.fail_heaters_var.get())
        self.plant.set_failure("rod_stuck", self.fail_rods_var.get())
        self.plant.set_failure("rcs_leak", self.fail_leak_var.get())
        
        # Feedback visual simples
        if any(self.plant.failures.values()):
            self.lbl_advisor.configure(text="ALERTA: FALHA NO SISTEMA DETECTADA!", foreground="red", background="yellow")

    def run_simulation_loop(self):
        print("Iniciando loop de simulação...")
        while self.plant.run_simulation:
            try:
                self.plant.update_physics(dt=0.1)
                self.plant.check_protection_system()
            except Exception as e:
                print(f"Erro na simulação: {e}")
            time.sleep(0.1) # 10Hz simulation rate

    def update_gui(self):
        # Atualizar Histórico para Gráficos
        # Adiciona os valores atuais nas listas para serem desenhados
        self.graph_history_pwr.append(self.plant.rx_power)
        self.graph_history_tavg.append(self.plant.rcs_avg_temp)
        self.graph_history_press.append(self.plant.prz_pressure)
        
        # Manter apenas os últimos 200 pontos (Janela deslizante)
        if len(self.graph_history_pwr) > 200:
            self.graph_history_pwr.pop(0)
            self.graph_history_tavg.pop(0)
            self.graph_history_press.pop(0)

        # Atualizar labels com valores da planta (Interface Gráfica)
        self.rx_power_var.set(f"{self.plant.rx_power:.2f}")
        self.prz_pressure_var.set(f"{self.plant.prz_pressure:.2f}")
        self.prz_level_var.set(f"{self.plant.prz_level:.1f}")
        self.rcs_temp_var.set(f"{self.plant.rcs_avg_temp:.1f}")
        self.tref_var.set(f"{self.plant.t_ref:.1f}")
        self.boron_var.set(f"{self.plant.boron_concentration:.0f}")
        self.vct_level_var.set(f"{self.plant.vct_level:.1f}")
        self.mw_var.set(f"{self.plant.electric_power:.1f}")
        self.steam_pressure_var.set(f"{self.plant.steam_pressure:.1f}")
        self.turbine_load_var.set(f"{self.plant.turbine_load:.1f}")
        
        # Lógica do Advisor (Sugestão de Operação)
        # Objetivo: Manter Barras de Controle entre 75% e 90% (Faixa Ideal de Controle)
        rods = self.plant.rods_position
        
        # Delta T (Diferença entre Potência Gerada e Carga da Turbina)
        # Se Tavg estiver caindo muito, significa que Carga > Potência Nuclear
        tavg_mismatch = self.plant.rcs_avg_temp - (290.0 + (self.plant.rx_power / 100.0) * 20.0)
        
        msg = ""
        alert_style = False
        
        if self.plant.reactor_trip:
             msg = "ALERTA: REATOR TRIPPED - Verifique Condições"
             alert_style = True
        elif abs(tavg_mismatch) > 2.0:
             if tavg_mismatch < 0:
                 msg = "ALERTA: Tavg BAIXA! Aumente Potência ou Reduza Carga"
             else:
                 msg = "ALERTA: Tavg ALTA! Reduza Potência ou Aumente Carga"
             alert_style = True
        elif rods < 75:
            # Barras muito inseridas -> Precisamos retirar barras -> Adicionar veneno químico (Boro) para compensar
            msg = "SUGESTÃO: BORAR (Barras muito inseridas < 75%)"
            alert_style = True
        elif rods > 95:
            # Barras muito extraídas -> Precisamos inserir barras -> Remover veneno químico (Diluir) para compensar
            msg = "SUGESTÃO: DILUIR (Barras muito extraídas > 95%)"
            alert_style = True
        else:
            msg = "SISTEMA: Operação Estável (Barras na faixa ideal)"
            
        self.advisor_var.set(msg)
        
        # Atualiza Estilo do Advisor
        if alert_style:
            self.lbl_advisor.configure(foreground="red", background="yellow")
        else:
            self.lbl_advisor.configure(foreground="purple", background=self.vars_frame.cget("background")) # Reset (pode precisar de ajuste dependendo do tema)

        # Atualiza Status
        if self.plant.reactor_trip:
            self.lbl_status.config(text="TRIPPED", foreground="red")
            # Atualiza visualização das barras (elas caem no trip)
            self.rods_display_var.set(f"{self.plant.rods_position:.1f}%")
            self.rods_progress['value'] = self.plant.rods_position
            
            # Popup de Alerta (Apenas uma vez)
            if not self.trip_alert_shown:
                self.trip_alert_shown = True
                self.plant.run_simulation = False # Parar a simulação física imediatamente
                
                reasons = "\n".join(self.plant.last_trip_reasons)
                messagebox.showerror("TRIP DO REATOR", f"O Sistema de Proteção desligou o reator!\n\nMotivos:\n{reasons}")
                
                if messagebox.askyesno("Fim da Simulação", "O Reator desligou (Trip). Deseja salvar o histórico desta sessão?"):
                    self.plant.save_current_session()
                    messagebox.showinfo("Salvo", "Dados salvos com sucesso!")
        else:
            self.lbl_status.config(text="NORMAL", foreground="green")
            # Atualiza visualização contínua (caso haja automação futura)
            self.rods_display_var.set(f"{self.plant.rods_position:.1f}%")
            self.rods_progress['value'] = self.plant.rods_position
            self.trip_alert_shown = False # Resetar flag se o reator for reiniciado (futuro)
            
        # Reagendar atualização (Loop da GUI)
        self.root.after(100, self.update_gui)

    def update_graphs_loop(self):
        self.canvas.delete("all")
        
        # Dimensões
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100: w = 600 
        if h < 100: h = 200
        
        # Dividi em 3 áreas (horizontalmente para economizar altura vertical)
        w_graph = w / 3
        
        # Desenha Gráfico 1: Potência (0-120%)
        self.draw_single_graph(0, 0, w_graph, h, self.graph_history_pwr, 0, 120, "Potência (%)", "cyan")
        
        # Desenha Gráfico 2: Tavg (280-330)
        self.draw_single_graph(w_graph, 0, w_graph, h, self.graph_history_tavg, 280, 330, "Tavg (°C)", "orange")
        
        # Desenha Gráfico 3: Pressão (140-170)
        self.draw_single_graph(2*w_graph, 0, w_graph, h, self.graph_history_press, 140, 170, "Pressão (Kg/cm²)", "lime")
        
        self.root.after(200, self.update_graphs_loop)

    def draw_single_graph(self, x, y, w, h, data, min_val, max_val, title, color):
        # Fundo e Bordas
        self.canvas.create_rectangle(x, y, x+w, y+h, outline="gray")
        self.canvas.create_text(x+10, y+10, text=f"{title} - Atual: {data[-1]:.1f}" if data else title, fill=color, anchor="nw", font=("Consolas", 10, "bold"))
        
        if not data: return
        
        # Escala
        range_val = max_val - min_val
        if range_val == 0: range_val = 1
        
        step_x = w / (len(data) - 1) if len(data) > 1 else w
        
        points = []
        for i, val in enumerate(data):
            px = x + i * step_x
            # Inverter Y (0 no topo)
            # Normalizar valor (0 a 1)
            norm_val = (val - min_val) / range_val
            # Clamp visual (para não sair do gráfico)
            if norm_val < 0: norm_val = 0
            if norm_val > 1: norm_val = 1
            
            py = y + h - (norm_val * h)
            points.append(px)
            points.append(py)
            
        if len(points) >= 4:
            self.canvas.create_line(points, fill=color, width=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = NuclearPlantGUI(root)
    root.mainloop()
