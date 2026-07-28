<div align="center">

# ☢️ Nuclear Plant Simulator

### Interactive PWR Nuclear Power Plant Simulator

A Python-based simulator of a **Pressurized Water Reactor (PWR)** designed for educational purposes and studies of nuclear reactor protection systems.

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-2E8B57?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

</div>

---

# 📖 About

**Nuclear Plant Simulator** is an interactive simulator of a simplified **Pressurized Water Reactor (PWR)** developed entirely in **Python**.

The application reproduces the behavior of the reactor core, primary and secondary coolant systems, pressurizer, turbine, generator, and protection systems, allowing users to operate the plant through a graphical interface while monitoring the main process variables in real time.

The simulator was created to integrate concepts of **Nuclear Engineering**, **Instrumentation and Control**, **Object-Oriented Programming**, and **Computer Simulation** into a single educational application.

---

# ✨ Main Features

## ☢️ Reactor Simulation

- Simplified PWR reactor model
- Reactor Core simulation
- Primary Cooling System (RCS)
- Secondary Steam Cycle
- Pressurizer simulation
- Turbine and Generator
- Boron concentration control
- Manual and automatic reactor operation

---

## 📊 Real-Time Monitoring

Monitor important plant variables, including:

- Reactor Power
- Average Coolant Temperature
- Pressurizer Pressure
- Pressurizer Level
- Steam Pressure
- Turbine Load
- Electrical Power
- Boron Concentration
- Volume Control Tank (VCT)

---

## 📈 Live Charts

The interface continuously displays:

- Reactor Power
- Average Temperature
- Pressurizer Pressure

allowing operators to observe plant behavior during normal operation and transient conditions.

---

## 🎮 Operator Controls

The simulator allows the operator to:

- Insert or withdraw control rods
- Enable automatic rod control
- Increase boron concentration
- Dilute reactor coolant
- Adjust turbine load
- Perform a manual reactor trip
- Restart the simulation
- Save simulation logs

---

# 🚨 Reactor Protection System (RPS)

The built-in Reactor Protection System continuously monitors plant conditions.

Automatic reactor shutdown (SCRAM) occurs whenever operational safety limits are exceeded.

Implemented protection signals include:

- High Reactor Power
- High Pressurizer Pressure
- Low Pressurizer Pressure
- High Pressurizer Level

---

# 💥 Failure Simulation

Training scenarios currently implemented:

- Pressurizer Spray Stuck Open
- Pressurizer Heater Failure
- Stuck Control Rods
- Loss Of Coolant Accident (LOCA)

These failures allow users to practice abnormal operating conditions in a safe virtual environment.

---

# 💾 Data Logging

Simulation sessions can be stored in an SQLite database.

Stored information includes:

- Simulation start time
- Simulation end time
- Final reactor status
- Reactor Trip cause
- Operator actions
- Alarm history
- Operational events

---

# 🏗️ System Architecture

```text
                    Operator
                        │
                        ▼
                Tkinter Interface
                        │
                        ▼
                 NuclearPlant
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
 Reactor Core   Primary System   Secondary System
        │             │             │
        └─────────────┼─────────────┘
                      ▼
        Reactor Protection System
                      │
                      ▼
           Logger + SQLite Database
```

---

# 📂 Project Structure

```text
NuclearPlantSimulator/

├── simulator.py
├── tk_gui.py
├── trip_reactor.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

# 🛠️ Technologies

- Python
- Tkinter
- SQLite
- Threading
- Object-Oriented Programming (OOP)
- PID Controllers
- Nuclear Engineering Concepts

---

# 🚀 Getting Started

Clone the repository:

```bash
git clone https://github.com/your-username/NuclearPlantSimulator.git
```

Enter the project folder:

```bash
cd NuclearPlantSimulator
```

Run the simulator:

```bash
python tk_gui.py
```

---

# 📚 Concepts Applied

- Pressurized Water Reactors (PWR)
- Reactor Protection System (RPS)
- Reactor Trip (SCRAM)
- Nuclear Instrumentation
- Process Control
- PID Controllers
- Thermodynamics
- Object-Oriented Programming
- SQLite Database
- Real-Time Simulation

---

# 🎯 Future Improvements

- Additional accident scenarios
- Steam Generator model
- Emergency Core Cooling System (ECCS)
- Containment simulation
- Operator performance reports
- Historical trend analysis
- Advanced alarm management
- SCADA-style interface

---

# 👩‍💻 Author

**Julia Terra**

Nuclear Engineering Undergraduate

Federal University of Rio de Janeiro (UFRJ)

---

# 📄 License

This project is licensed under the **MIT License**.

---

<div align="center">

⭐ If you found this project interesting, consider giving it a star!

Developed for academic, educational and research purposes.

</div>
