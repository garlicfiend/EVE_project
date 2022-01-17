import tkinter as tk
from tkinter import messagebox
from evedplot import *
import random
import json

# GUI Color Palette
WIN_BG = '#070709'
BOX_BG = '#112027'
BUTTON_BG = '#1C3B4D'
SUB_FG = '#336A91'
FONT_FG = '#D3DCE5'
BUTTON_FG ='#4EA1D8'

FONT = ("Ariel", 14)

current_system = None
current_goal = None
jump_to = None
agents = {}
missions = {}
system_names = SYSTEMS['SOLARSYSTEMNAME'].tolist()
player = Player(current_system)

with open("pathlog.txt", "w") as file:
    file.write("LOG BEGIN\n")


def set_current_system():

    # Bring in global variable
    global current_system

    # Get System from box
    cur_sys_input = current_system_entry.get().title()

    # Check if real system
    if cur_sys_input not in system_names:
        messagebox.showinfo(message=f"{cur_sys_input} is not a known system.")
        return
    else:
        # Update Global
        current_system = cur_sys_input
        # Update Player
        print(f"Current System: {current_system}")
        player.update_system(current_system)
        # Call update
        update_current_system()
        return


def update_current_system():
    global jump_to




    # Update Current Jump Path

    print(f"Agents: {agents}, \nMissions: {missions}")
    if agents or missions:
        # Update Jumps
        if agents:
            refresh_agents()
        if missions:
            refresh_missions()
        jump_data = player.get_next_jump(agents, missions)
        print(f"jump_to changed from {jump_to} to {jump_data[2]}; data returned: {jump_data}")
        jump_to = jump_data[2]

        update_goal()

    # Update Label
    cur_sys_label.config(text=f"CURRENT SYSTEM: {current_system}")
    # Reset entry box
    current_system_entry.delete(0, tk.END)


def add_agent():
    # Grab Agent Name From Box
    agent_name = agent_name_entry.get().title()

    # Check if agent already in list
    is_there = False
    for agent in agents:
        if agents[agent].name_match(agent_name):
            is_there = True

    # Get Agent's System from box
    agent_system = agent_system_entry.get().title()

    # Check to see if real system - cancel entry if not
    if agent_system not in system_names:
        messagebox.showinfo(message=f"{agent_system} is not a known system.")
        return

    # If Agent already in list cancel entry
    elif is_there:
        messagebox.showinfo(message=f"{agent_name} already exists.")
        return

    # Add new agent to list
    else:
        # Get Jumps from box
        agent_jumps = int(agent_jumps_entry.get())

        # Add new
        agents[agent_name] = Agent(agent_name, agent_system, agent_jumps)

        # Call Refresh
        refresh_agents()

        # update save file
        save_data()

        # Reset Entry Boxes
        agent_name_entry.delete(0, tk.END)
        agent_name_entry.insert(tk.END, string="Agent Name")
        agent_system_entry.delete(0, tk.END)
        agent_system_entry.insert(tk.END, string="Agent System")
        agent_jumps_entry.delete(0, tk.END)
        agent_jumps_entry.insert(tk.END, string="Jumps")
        return


def add_mission():

    # Get info from boxes
    miss_agent = mission_agent_entry.get()
    miss_dest = mission_destination_entry.get()
    miss_jumps = int(mission_jumps_entry.get())

    # Check system entry
    if miss_dest not in system_names:
        messagebox.showinfo(message=f"{mission_destination_entry} is not a known system.")
        return

    # Check to see if Mission Agent exists
    if miss_agent not in agents:
        messagebox.showinfo(message=f"Please add {mission_agent_entry.get()} as an Agent.")
        return

    # Create Mission ID
    rand_id = random.randint(10000, 99999)
    while rand_id in missions:
        rand_id = random.randint(10000, 99999)

    # Add New Mission to Missions global dict
    new_mission = Mission(miss_agent, miss_dest, rand_id, miss_jumps)
    missions[rand_id] = new_mission

    # Add Mission to Agent's mission list, set Agent's status to Active
    agents[miss_agent].add_mission(new_mission)

    # Update save file
    save_data()

    # Refresh agents and missions
    refresh_agents()
    refresh_missions()

    # Reset Entry Boxes
    mission_agent_entry.delete(0, tk.END)
    mission_agent_entry.insert(tk.END, string="Mission Agent")
    mission_destination_entry.delete(0, tk.END)
    mission_destination_entry.insert(tk.END, string="Destination")
    mission_jumps_entry.delete(0, tk.END)
    mission_jumps_entry.insert(tk.END, string="Jumps")

    return


def complete_mission():

    # Get info from boxes
    m_id = int(mission_id_entry.get())
    m_agent = missions[m_id].agent

    # call Complete Mission on mission agent
    agents[m_agent].complete_mission(m_id)

    # Remove Mission from Missions global dict
    del missions[m_id]

    # Refresh agents and missions
    refresh_agents()
    refresh_missions()

    # Update Save File
    save_data()


def activate_agent():

    # Check if Agent exists
    if activate_agent_entry.get() not in agents:
        messagebox.showinfo(message=f"{activate_agent_entry.get()} is not an Agent.")
        return
    else:
        # Set agent status
        agents[activate_agent_entry.get()].status = "waiting"

        # Refresh agents
        refresh_agents()

        # Update Save File
        save_data()
        return


def refresh_agents():

    # Create a list for waiting agents
    waiting_agents = []

    # Create output strings
    wait_agents = ""
    wait_systems = ""

    # Calculate path for each waiting agent
    # Append to wait list (name, system) for each agent
    for agent in agents:
        if agents[agent].status == "waiting":
            player.make_path(agents[agent].system, agents[agent].jumps)
            waiting_agents.append(agents[agent].wait_stats())

    # Update Goal
    update_goal()

    # Build output strings
    for item in waiting_agents:
        wait_agents += item[0] + "\n"
        wait_systems += str(item[1]) + "|" + item[2] + "\n"

    # Delete and update display boxes
    waiting_agents_agent_textbox.delete('1.0', tk.END)
    waiting_agents_agent_textbox.insert(tk.END, wait_agents)
    waiting_agents_system_textbox.delete('1.0', tk.END)
    waiting_agents_system_textbox.insert(tk.END, wait_systems)


def refresh_missions():

    # Create Output Strings
    act_id = ""
    act_agents = ""
    act_dest = ""

    # Calculate path for each waiting agent
    # Populate Output Strings
    for mission in missions:
        player.make_path(missions[mission].system, missions[mission].jumps)
        act_id += str(missions[mission].missionid) + "\n"
        act_agents += missions[mission].agent + "\n"
        act_dest += str(missions[mission].jumps) + "|" + missions[mission].system + "\n"

    # Update Current Goal
    update_goal()

    # Delete and update display boxes
    active_missions_id_textbox.delete('1.0', tk.END)
    active_missions_id_textbox.insert(tk.END, act_id)
    active_missions_agent_textbox.delete('1.0', tk.END)
    active_missions_agent_textbox.insert(tk.END, act_agents)
    active_missions_destination_textbox.delete('1.0', tk.END)
    active_missions_destination_textbox.insert(tk.END, act_dest)


def update_next_jump():
    # GOING TO REMOVE ALL THIS - CHANGE LIST TO SINGLE DESTINATION / DISTANCE BOX
    next_jump = player.get_next_jump(agents, missions)
    global jump_to
    jump_to = next_jump[1]
    if next_jump[0] == 0:
        current_destination_label.config(text=f"Current Destination: !!{current_goal}!!")

    # next_system_te=0-xtbox.delete('1.0', tk.END)
    # next_system_textbox.insert(tk.END, list_display)


def jump():
    global current_system
    global jump_to
    print(f"{current_system} changed to {jump_to}")
    current_system = jump_to
    # Update Player
    print(f"Current System: {current_system}")
    player.update_system(current_system)
    player.update_jumps(agents)
    player.update_jumps(missions)
    update_current_system()


def update_goal():
    global current_goal
    new_data = player.get_next_jump(agents, missions)
    current_goal = new_data[1]
    player.goal = current_goal
    if current_system == current_goal:
        current_destination_label.config(text=f"Current Destination: !!{current_goal}!!")
    else:
        current_destination_label.config(text=f"Current Destination: {current_goal}")
    current_destination_distance_label.config(text=f"Distance: {new_data[0]}")


def save_data():

    # Create save dict for agents
    agent_dict = {}
    # get save data for each agent
    for agent in agents:
        agent_dict[agent] = agents[agent].save_dump()

    # Create save dict for missions
    mission_dict = {}
    # get save data from each mission
    for mission in missions:
        mission_dict[mission] = missions[mission].save_dump()

    # Create Master Dict to write to JSON file
    save_dict = {
        "current_system": current_system,
        "agents": agent_dict,
        "missions": mission_dict
    }

    # Write Master Dict to File
    with open("evedplot.json", mode="w") as file:
        json.dump(save_dict, file, indent= 4)



def load_data():

    # Global Variables to Set
    global current_system
    global agents
    global missions

    try:
        # load JSON from file as dict
        with open("evedplot.json", mode="r") as file:
            load_dict = json.load(file)

    except json.decoder.JSONDecodeError:
        pass

    else:
        # Set Current System
        current_system = load_dict['current_system']
        # Update Player
        print(f"Current System: {current_system}")
        player.update_system(current_system)
        update_current_system()

        # Repopulate Agents
        for agent in load_dict['agents']:
            new_agent = Agent(
                load_dict['agents'][agent]['name'],
                load_dict['agents'][agent]['system'],
                load_dict['agents'][agent]['jumps'],
                load_dict['agents'][agent]['status'],
            )
            agents[new_agent.name] = new_agent
        refresh_agents()

        # Repopulate Missions
        for mission in load_dict['missions']:
            new_mission = Mission(
                load_dict['missions'][mission]['agent'],
                load_dict['missions'][mission]['destination'],
                load_dict['missions'][mission]['missionid'],
                load_dict['missions'][mission]['jumps']
            )
            missions[new_mission.missionid] = new_mission
            agents[load_dict['missions'][mission]['agent']].add_mission(new_mission)
        refresh_missions()

        update_current_system()


# ----------------------------------------------------------------
# ----------GUI---------------------------------------------------
# ----------------------------------------------------------------

window = tk.Tk()
window.title("Eve Delivery Plotter")
window.config(padx=20, pady=20, bg=WIN_BG)

# -------------------:

# Current System Label
cur_sys_label = tk.Label(text=f"CURRENT SYSTEM: {current_system}", font=FONT, bg=WIN_BG, fg=FONT_FG)
cur_sys_label.grid(column=0, row=0, columnspan=2)

# Set Current System Box
current_system_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
current_system_entry.insert(tk.END, string="System")
current_system_entry.grid(column=2, row=0)

# Set Current System Button
current_system_button = tk.Button(text="Add", command=set_current_system, bg=BUTTON_BG, fg=BUTTON_FG)
current_system_button.grid(column=4, row=0)

# -------------------:

# Current Destination Label
current_destination_label = tk.Label(text=f"Current Destination: {current_goal}", font=FONT, bg=WIN_BG, fg=FONT_FG)
current_destination_label.grid(column=0, row=1, columnspan=2)

# Current Destination Distance Label
current_destination_distance_label = tk.Label(text=f"Distance: None", font=FONT, bg=WIN_BG, fg=FONT_FG)
current_destination_distance_label.grid(column=2, row=1)

# Current Destination Button
current_destination_button = tk.Button(text="Jump", command=jump, bg=BUTTON_BG, fg=BUTTON_FG)
current_destination_button.grid(column=4, row=1)

# -------------------:


# Add Agent Label
add_agent_label = tk.Label(text="Add Agent:", font=FONT, bg=WIN_BG, fg=FONT_FG)
add_agent_label.grid(column=0, row=2)

# Add Agent Name Box
agent_name_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
agent_name_entry.insert(tk.END, string="Agent Name")
agent_name_entry.grid(column=1, row=2)

# Add Agent System Box
agent_system_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
agent_system_entry.insert(tk.END, string="Agent System")
agent_system_entry.grid(column=2, row=2)

# Add Agent Jumps Box
agent_jumps_entry = tk.Entry(width=6, bg=BOX_BG, fg=SUB_FG)
agent_jumps_entry.insert(tk.END, string="Jumps")
agent_jumps_entry.grid(column=3, row=2)

# Add Agent Button
add_agent_button = tk.Button(text="Add", command=add_agent, bg=BUTTON_BG, fg=BUTTON_FG)
add_agent_button.grid(column=4, row=2)

# -------------------:

# Add Mission Label
add_mission_label = tk.Label(text="Add Mission:", font=FONT, bg=WIN_BG, fg=FONT_FG)
add_mission_label.grid(column=0, row=3)

# Add Mission Agent Box
mission_agent_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
mission_agent_entry.insert(tk.END, string="Mission Agent")
mission_agent_entry.grid(column=1, row=3)

# Add Mission Destination Box
mission_destination_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
mission_destination_entry.insert(tk.END, string="Destination")
mission_destination_entry.grid(column=2, row=3)

# Add Mission Jumps Box
mission_jumps_entry = tk.Entry(width=6, bg=BOX_BG, fg=SUB_FG)
mission_jumps_entry.insert(tk.END, string="Jumps")
mission_jumps_entry.grid(column=3, row=3)

# Add Mission Button
add_mission_button = tk.Button(text="Add", command=add_mission, bg=BUTTON_BG, fg=BUTTON_FG)
add_mission_button.grid(column=4, row=3)

# -------------------:

# Complete Mission Label
complete_mission_label = tk.Label(text="Complete Mission:", font=FONT, bg=WIN_BG, fg=FONT_FG)
complete_mission_label.grid(column=1, row=4)

# Complete Mission ID Box
mission_id_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
mission_id_entry.insert(tk.END, string="Mission ID#")
mission_id_entry.grid(column=2, row=4)

# Complete Mission Button
complete_mission_button = tk.Button(text="Complete", command=complete_mission, bg=BUTTON_BG, fg=BUTTON_FG)
complete_mission_button.grid(column=4, row=4)

# -------------------:

# Waiting Agents Label
waiting_agents_label = tk.Label(text="Waiting Agents", font=FONT, bg=WIN_BG, fg=FONT_FG)
waiting_agents_label.grid(column=0, row=5, columnspan=2)

# Waiting Agents Agent Box
waiting_agents_agent_textbox = tk.Text(height=8, width=20, bg=BOX_BG, fg=BUTTON_FG)
waiting_agents_agent_textbox.grid(column=0, row=6, columnspan=1)

# Waiting Agents System Box
waiting_agents_system_textbox = tk.Text(height=8, width=20, bg=BOX_BG, fg=BUTTON_FG)
waiting_agents_system_textbox.grid(column=0, row=6, columnspan=3)

# # Waiting Agents Distance Box
# waiting_agents_distance_textbox = tk.Text(height=8, width=5, bg=BOX_BG, fg=BUTTON_FG)
# waiting_agents_distance_textbox.grid(column=3, row=6, columnspan=1)

# -------------------:

# Active Missions Label
active_missions_label = tk.Label(text="Active Missions", font=FONT, bg=WIN_BG, fg=FONT_FG)
active_missions_label.grid(column=2, row=5, columnspan=3)

# Active Missions ID Box
active_missions_id_textbox = tk.Text(height=8, width=7, bg=BOX_BG, fg=BUTTON_FG)
active_missions_id_textbox.grid(column=2, row=6, columnspan=1, sticky=tk.W)

# Active Missions Agent Box
active_missions_agent_textbox = tk.Text(height=8, width=16, bg=BOX_BG, fg=BUTTON_FG)
active_missions_agent_textbox.grid(column=2, row=6, columnspan=2, sticky=tk.E)

# Active Missions Destination Box
active_missions_destination_textbox = tk.Text(height=8, width=15, bg=BOX_BG, fg=BUTTON_FG)
active_missions_destination_textbox.grid(column=4, row=6, columnspan=4)

# # Active Missions Distance Box
# active_missions_distance_textbox = tk.Text(height=8, width=5, bg=BOX_BG, fg=BUTTON_FG)
# active_missions_distance_textbox.grid(column=3, row=8, columnspan=1)

# -------------------:

# Activate Agent Label
activate_agent_label = tk.Label(text="Reactivate Agent:", font=FONT, bg=WIN_BG, fg=FONT_FG)
activate_agent_label.grid(column=1, row=9)

# Activate Agent Box
activate_agent_entry = tk.Entry(width=20, bg=BOX_BG, fg=SUB_FG)
activate_agent_entry.insert(tk.END, string="Agent Name")
activate_agent_entry.grid(column=2, row=9)

# Activate Agent Button
activate_agent_button = tk.Button(text="Activate", command=activate_agent, bg=BUTTON_BG, fg=BUTTON_FG)
activate_agent_button.grid(column=3, row=9)

# --------------------------------------------------------------------

load_data()

player.dump_path_names()

# holder = player.get_next_jump(agents, missions)
#
# print(f"next_jump = {holder}")

window.mainloop()