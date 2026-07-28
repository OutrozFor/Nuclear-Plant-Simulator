import time
import random
import sqlite3
from datetime import datetime

# --- Persistência e Logging (Banco de Dados) ---
# Essa classe gerencia toda a conexão com o banco de dados SQLite.
# Eu escolhi usar SQLite por ser leve e não precisar de servidor instalado.
class DatabaseHandler:
    def __init__(self, db_name="nuclear_simulation.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    # Cria as tabelas se elas ainda não existirem
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                final_status TEXT,
                trip_reason TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id INTEGER,
                timestamp TEXT,
                event_type TEXT,
                message TEXT,
                rx_power REAL,
                prz_pressure REAL,
                avg_temp REAL,
                FOREIGN KEY(simulation_id) REFERENCES simulations(id)
            )
        ''')
        self.conn.commit()

    # Salva a sessão completa de uma vez só (Bulk Insert) para ser mais rápido
    def save_session(self, start_time, end_time, status, trip_reason, logs):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO simulations (start_time, end_time, final_status, trip_reason)
                VALUES (?, ?, ?, ?)
            ''', (start_time, end_time, status, trip_reason))
            sim_id = cursor.lastrowid
            
            # Prepara os dados para inserir tudo de uma vez na tabela de logs
            log_data = [(sim_id, l['timestamp'], l['type'], l['message'], l['power'], l['pressure'], l['temp']) for l in logs]
            cursor.executemany('''
                INSERT INTO logs (simulation_id, timestamp, event_type, message, rx_power, prz_pressure, avg_temp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', log_data)
            
            self.conn.commit()
            print(f"[DB] Simulação {sim_id} salva com sucesso ({len(logs)} eventos).")
        except Exception as e:
            print(f"[DB] Erro ao salvar simulação: {e}")

# Classe para guardar os logs na memória RAM durante a simulação.
# Isso evita ficar escrevendo no disco a cada milissegundo, o que deixaria o simulador lento.
class SimulationLogger:
    def __init__(self):
        self.logs = []
        self.start_time = datetime.now().isoformat()

    def log(self, event_type, message, plant):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'power': plant.rx_power,
            'pressure': plant.prz_pressure,
            'temp': plant.rcs_avg_temp
        }
        self.logs.append(entry)
        # Print console para debug (ajuda a ver o que está acontecendo enquanto roda)
        print(f"[LOG] {event_type}: {message}")

    def get_logs(self):
        return self.logs
    
    def reset(self):
        self.logs = []
        self.start_time = datetime.now().isoformat()

# --- Conceitos de POO: Herança e Abstração ---
class SystemComponent:
    """ Classe base abstrata para componentes da usina """
    def update(self, dt):
        pass
    
    def reset(self):
        pass

# --- Conceitos de POO: Encapsulamento ---
# Implementação de um controlador PID genérico para controlar Nível e Pressão.
# PID = Proporcional, Integral, Derivativo. É o padrão da indústria para controle.
class PIDController:
    def __init__(self, kp, ki, kd, min_out=-100, max_out=100):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_out = min_out
        self.max_out = max_out
        self.setpoint = 0
        self.integral = 0
        self.last_error = 0

    def compute(self, measurement, dt):
        error = self.setpoint - measurement
        self.integral += error * dt
        
        # Anti-windup: Impede que o termo integral cresça infinitamente se o atuador saturar
        if self.integral > self.max_out: self.integral = self.max_out
        if self.integral < self.min_out: self.integral = self.min_out
            
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error
        
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        
        # Saturação da saída (limites físicos do atuador)
        if output > self.max_out: output = self.max_out
        if output < self.min_out: output = self.min_out
            
        return output
    
    def reset(self):
        self.integral = 0
        self.last_error = 0

class ReactorCore(SystemComponent):
    """ Representa o núcleo do reator (Cinética e Controle de Barras) """
    def __init__(self):
        self.power = 100.0
        self.rods_position = 50.0
        self.boron_concentration = 1000.0
        self.auto_rods = False
        self.t_ref = 310.0

    def update(self, dt, failures):
        # Cálculo simplificado da reatividade (Física de Nêutrons)
        # Barras inseridas (posição menor) diminuem a potência.
        # Boro alto diminui a potência.
        reactivity_rods = (self.rods_position - 50.0) * 0.001 
        reactivity_boron = (1000.0 - self.boron_concentration) * 0.0005
        reactivity = reactivity_rods + reactivity_boron
        
        # Equação cinética pontual simplificada
        self.power += reactivity * self.power * dt
        self.power += random.uniform(-0.1, 0.1) # Ruído natural do processo
        
        if self.power < 0: self.power = 0
        if self.power > 120: self.power = 120

    def control_rods(self, dt, current_temp, turbine_load, failures):
        # Tref (Temperatura de Referência) varia com a carga da turbina (Programa de Tavg)
        self.t_ref = 290.0 + (turbine_load / 100.0) * 20.0
        
        # Lógica do Controle Automático de Barras
        if self.auto_rods:
            temp_error = current_temp - self.t_ref
            # Deadband de 0.5 graus para evitar oscilação excessiva
            if abs(temp_error) > 0.5:
                rod_speed = -temp_error * 0.5
                if rod_speed > 5.0: rod_speed = 5.0
                if rod_speed < -5.0: rod_speed = -5.0
                
                # Se a falha de barra travada não estiver ativa, move as barras
                if not failures.get("rod_stuck", False):
                    self.rods_position += rod_speed * dt
                
                if self.rods_position > 100: self.rods_position = 100
                if self.rods_position < 0: self.rods_position = 0

    def reset(self):
        self.power = 100.0
        self.rods_position = 50.0
        self.boron_concentration = 1000.0
        self.auto_rods = False

class PrimarySystem(SystemComponent):
    """ Representa o Loop Primário (RCS, Pressurizador, VCT) """
    def __init__(self):
        self.pressure = 155.0
        self.level = 50.0
        self.avg_temp = 310.0
        self.vct_level = 60.0
        self.containment_pressure = 0.0
        
        # Composição: O sistema primário TEM controladores PID para manter estabilidade
        self.pid_level = PIDController(kp=2.0, ki=0.1, kd=0.5)
        self.pid_pressure = PIDController(kp=5.0, ki=0.2, kd=1.0)

    def update(self, dt, core_power, turbine_load, failures):
        # Termodinâmica: Balanço de Energia
        # Se Potência Nuclear > Carga Turbina -> Temperatura sobe
        # Se Potência Nuclear < Carga Turbina -> Temperatura desce
        power_mismatch = core_power - turbine_load
        self.avg_temp += power_mismatch * 0.05 * dt
        if self.avg_temp > 350: self.avg_temp = 350
        if self.avg_temp < 200: self.avg_temp = 200
        
        # Controle de Nível do Pressurizador
        # O Setpoint de nível varia com a potência (Programa de Nível)
        level_setpoint = 25.0 + (core_power / 100.0) * 35.0
        self.pid_level.setpoint = level_setpoint
        level_action = self.pid_level.compute(self.level, dt)
        
        # Expansão térmica da água afeta o nível
        thermal_expansion = (self.avg_temp - 290.0) * 1.75 - (self.level - 25.0)
        mass_flow = level_action * 0.05
        self.level += (thermal_expansion * 0.1 + mass_flow) * dt
        
        # Balanço de massa com o VCT (Volume Control Tank)
        self.vct_level -= mass_flow * 2.0 * dt
        if self.vct_level > 100: self.vct_level = 100
        if self.vct_level < 0: self.vct_level = 0
        
        # Controle de Pressão do Pressurizador
        self.pid_pressure.setpoint = 155.0
        pressure_action = self.pid_pressure.compute(self.pressure, dt)
        
        # Simulação de Falhas no Controle de Pressão
        if failures.get("spray_stuck_open", False):
            pressure_action = -100.0 # Spray aberto reduz pressão drasticamente
        elif failures.get("heaters_fail", False) and pressure_action > 0:
            pressure_action = 0.0 # Aquecedores não funcionam para subir pressão
            
        level_effect = (self.level - level_setpoint) * 0.2
        control_effect = pressure_action * 0.1
        heat_loss = -0.05
        
        # Simulação de Vazamento (LOCA - Loss of Coolant Accident)
        leak_effect = 0.0
        if failures.get("rcs_leak", False):
            leak_effect = -2.0
            self.level -= 0.5 * dt
            self.containment_pressure += 0.01 * dt # Pressão no contimento sobe
            
        self.pressure += (level_effect + control_effect + heat_loss + leak_effect) * dt
        self.pressure += random.uniform(-0.05, 0.05)

    def reset(self):
        self.pressure = 155.0
        self.level = 50.0
        self.avg_temp = 310.0
        self.vct_level = 60.0
        self.containment_pressure = 0.0
        self.pid_level.reset()
        self.pid_pressure.reset()

class SecondarySystem(SystemComponent):
    """ Representa o Loop Secundário (Turbina, Gerador, Vapor) """
    def __init__(self):
        self.steam_pressure = 60.0
        self.turbine_load = 100.0
        self.electric_power = 1000.0
        self.turbine_tripped = False

    def update(self, dt, core_power):
        if self.turbine_tripped:
            self.turbine_load = 0
            self.electric_power = 0
        else:
            efficiency = self.steam_pressure / 60.0
            if efficiency > 1.0: efficiency = 1.0
            self.electric_power = self.turbine_load * 10.0 * efficiency

        energy_balance = core_power - self.turbine_load
        self.steam_pressure += energy_balance * 0.1 * dt
        
        if self.steam_pressure > 80: self.steam_pressure = 80
        if self.steam_pressure < 0: self.steam_pressure = 0

    def reset(self):
        self.steam_pressure = 60.0
        self.turbine_load = 100.0
        self.electric_power = 1000.0
        self.turbine_tripped = False

# --- Conceitos de POO: Composição (A Planta TEM sistemas) ---
# Essa é a classe principal que agrega todos os subsistemas.
# Funciona como uma "Fachada" (Facade Pattern) para simplificar o uso pela GUI.
class NuclearPlant:
    def __init__(self):
        # Instanciando os subsistemas
        self.core = ReactorCore()
        self.primary = PrimarySystem()
        self.secondary = SecondarySystem()
        
        # Sistema de Logs e Banco de Dados
        self.db = DatabaseHandler()
        self.logger = SimulationLogger()
        
        self.failures = {
            "spray_stuck_open": False,
            "heaters_fail": False,
            "rod_stuck": False,
            "rcs_leak": False
        }
        
        self.reactor_trip = False
        self.last_trip_reasons = []
        self.run_simulation = True
        
        self.logger.log("INFO", "Sistema Inicializado", self)

    # --- Properties (Getters/Setters) para Interface Pública ---
    # Facade Pattern: Simplifica o acesso aos subsistemas para a GUI
    # A GUI não precisa saber que 'power' está dentro de 'core', ela pede para 'plant'.
    
    @property
    def rx_power(self): return self.core.power
    @rx_power.setter
    def rx_power(self, value): self.core.power = value

    @property
    def rods_position(self): return self.core.rods_position
    @rods_position.setter
    def rods_position(self, value): self.core.rods_position = value

    @property
    def boron_concentration(self): return self.core.boron_concentration
    @boron_concentration.setter
    def boron_concentration(self, value): self.core.boron_concentration = value
    
    @property
    def auto_rods(self): return self.core.auto_rods
    @auto_rods.setter
    def auto_rods(self, value): self.core.auto_rods = value
    
    @property
    def t_ref(self): return self.core.t_ref

    @property
    def prz_pressure(self): return self.primary.pressure
    @property
    def prz_level(self): return self.primary.level
    @property
    def rcs_avg_temp(self): return self.primary.avg_temp
    @property
    def vct_level(self): return self.primary.vct_level
    @property
    def containment_pressure(self): return self.primary.containment_pressure

    @property
    def steam_pressure(self): return self.secondary.steam_pressure
    @property
    def turbine_load(self): return self.secondary.turbine_load
    @property
    def electric_power(self): return self.secondary.electric_power

    # --- Métodos de Controle ---
    def update_physics(self, dt=1.0):
        # Se o reator estiver em Trip (desligado), a potência cai rapidamente (Decaimento)
        if self.reactor_trip:
            self.core.power = self.core.power * 0.85 # Scram
        else:
            # Atualiza física do núcleo
            self.core.update(dt, self.failures)
            # Atualiza controle automático de barras
            self.core.control_rods(dt, self.primary.avg_temp, self.secondary.turbine_load, self.failures)
            
        # Atualiza termodinâmica dos loops primário e secundário
        self.primary.update(dt, self.core.power, self.secondary.turbine_load, self.failures)
        self.secondary.update(dt, self.core.power)

    def check_protection_system(self):
        # Sistema de Proteção do Reator (RPS)
        # Verifica limites de segurança e dispara o Trip se necessário
        reasons = []
        if self.core.power > 109.0: reasons.append("Power Range High Flux (109%)")
        if self.primary.pressure > 167.72: reasons.append("Pressurizer High Pressure")
        if self.primary.pressure < 136.78: reasons.append("Pressurizer Low Pressure")
        if self.primary.level > 92.0: reasons.append("Pressurizer High Level")
        
        if reasons and not self.reactor_trip:
            self.trigger_trip(reasons)

    def trigger_trip(self, reasons):
        self.reactor_trip = True
        self.last_trip_reasons = reasons
        self.core.rods_position = 0.0 # Inserção total das barras (Gravidade)
        self.secondary.turbine_tripped = True # Trip da turbina acompanha trip do reator
        
        msg = f"TRIP DO REATOR: {', '.join(reasons)}"
        self.logger.log("TRIP", msg, self)
        print(f"\n[!!!] {msg}")

    def save_current_session(self):
        """ Salva a sessão atual no banco de dados """
        end_time = datetime.now().isoformat()
        status = "TRIPPED" if self.reactor_trip else "NORMAL"
        reason = ", ".join(self.last_trip_reasons) if self.last_trip_reasons else "N/A"
        
        self.db.save_session(self.logger.start_time, end_time, status, reason, self.logger.get_logs())
        print("\n[INFO] Log salvo no banco de dados.")

    def reset(self):
        # Resetar componentes
        self.core.reset()
        self.primary.reset()
        self.secondary.reset()
        self.reactor_trip = False
        self.last_trip_reasons = []
        for k in self.failures: self.failures[k] = False
        
        self.logger.reset()
        self.logger.log("INFO", "Simulação Reiniciada (Reset)", self)
        print("\n[INFO] Planta Reiniciada.")

    def set_failure(self, failure_name, active):
        """ Define uma falha e registra no log """
        if failure_name in self.failures:
            prev_state = self.failures[failure_name]
            self.failures[failure_name] = active
            if prev_state != active:
                status = "ATIVADA" if active else "DESATIVADA"
                self.logger.log("FAILURE", f"Falha {failure_name} {status}", self)

    def borate(self, amount):
        self.core.boron_concentration += amount
        self.logger.log("OPERATOR", f"Borar {amount} ppm", self)

    def dilute(self, amount):
        self.core.boron_concentration -= amount
        if self.core.boron_concentration < 0: self.core.boron_concentration = 0
        self.logger.log("OPERATOR", f"Diluir {amount} ppm", self)

    def set_turbine_load(self, load):
        prev = self.secondary.turbine_load
        self.secondary.turbine_load = load
        if self.secondary.turbine_load > 100: self.secondary.turbine_load = 100
        if self.secondary.turbine_load < 0: self.secondary.turbine_load = 0
        
        if abs(prev - self.secondary.turbine_load) > 1.0: # Log apenas mudanças significativas
            self.logger.log("OPERATOR", f"Carga Turbina ajustada para {self.secondary.turbine_load:.1f}%", self)

    def move_control_rods(self, delta):
        """ Move as barras de controle manualmente e registra no log """
        old_pos = self.core.rods_position
        new_pos = old_pos + delta
        
        # Limites físicos (0% a 100%)
        if new_pos > 100: new_pos = 100
        if new_pos < 0: new_pos = 0
        
        self.core.rods_position = new_pos
        
        if old_pos != new_pos:
            self.logger.log("OPERATOR", f"Barras movidas de {old_pos:.1f}% para {new_pos:.1f}% (Delta: {delta})", self)

if __name__ == "__main__":
    sim = NuclearPlant()
    # Loop de teste simples
    try:
        while True:
            sim.update_physics()
            sim.check_protection_system()
            print(f"\rPower: {sim.rx_power:.2f}% | Press: {sim.prz_pressure:.2f}", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
