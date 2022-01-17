import pandas

# Eve reference files
SYSTEMS = pandas.read_csv("mapSolarSystems.csv")
JUMPS = pandas.read_csv("mapSolarSystemJumps.csv")

# Dictionary for checking node efficiency for path search
check_dict = {}
# Global tracker for how many queries it takes to find a system
query_tracker = 0
log_file = None

# functions to get system names and ID's from csv files
def get_sys_id(sys_name):
    system_index = SYSTEMS.index[SYSTEMS.SOLARSYSTEMNAME == sys_name].item()
    return SYSTEMS.SOLARSYSTEMID[system_index]


def get_sys_name(sys_id):
    system_index = SYSTEMS.index[SYSTEMS.SOLARSYSTEMID == sys_id].item()
    return SYSTEMS.SOLARSYSTEMNAME[system_index]


class Agent:

    def __init__(self, name, system, jumps, status="waiting"):
        self.name = name
        self.system = system
        self.missions = {}
        self.status = status
        self.jumps = jumps

    def add_mission(self, mission):
        self.missions[mission.missionid] = mission
        self.status = 'active'

    def get_missions(self):
        return self.missions

    def complete_mission(self, m_id):
        del self.missions[m_id]
        if not self.missions:
            self.status = "inactive"

    def name_match(self, name):
        if name == self.name:
            return True
        else:
            return False

    def wait_stats(self):
        return (self.name, self.jumps, self.system)

    def save_dump(self):
        save_dict = {}
        save_missions = []
        save_dict["name"] = self.name
        save_dict["system"] = self.system
        save_dict["status"] = self.status
        save_dict["jumps"] = self.jumps
        for mission in self.missions:
            save_missions.append(self.missions[mission].missionid)
        save_dict["missions"] = save_missions
        return save_dict


class Mission:

    def __init__(self, agent, destination, id, jumps):
        self.agent = agent
        self.system = destination
        self.missionid = id
        self.jumps = jumps

    def save_dump(self):
        return {
            "agent": self.agent,
            "destination": self.system,
            "missionid": self.missionid,
            "jumps": self.jumps
        }


class System:

    def __init__(self, name):
        self.name = name
        self.system_id = get_sys_id(self.name)
        self.stargates = self.get_stargates()
        self.current_score = None

    # Get Stargates from reference DataFrame
    def get_stargates(self):
        gates = JUMPS[JUMPS.FROMSOLARSYSTEMID == self.system_id]
        return gates["TOSOLARSYSTEMID"].tolist()

    def query_path(self, jumps_left, goal, from_id, query_id):

        # Bring in and iterate tracking variables
        global query_tracker
        query_tracker +=1
        query_id += 1

        # Bring in check_dict
        global check_dict

        # Tracking Print Statement
        with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{jumps_left}:{query_tracker} -{self.system_id}|{self.name}- *{goal}* +{self.stargates}+ Starting query\n")

        # Check if dead-end system
        if len(self.stargates) == 1:
            with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- Returning False - Deadspace\n")
            check_dict[self.system_id] = query_id
            return False

        # Check if connected to goal, if found, return self and goal in List
        elif goal in self.stargates:
            with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- FOUND GOAL; returning [{self.system_id}, {goal}]\n")
            return [self.system_id, goal]

        # Check if reached jump limit
        elif jumps_left == 1:
            with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- End Branch; returning False\n")
            check_dict[self.system_id] = query_id
            return False

        else:

            # Create list to return
            query_result = []

            # Were any new systems genned?
            sys_gen = False

            # Iterate through connections
            for gate in self.stargates:

                # Eliminate origin connection or redundant node
                gate_check = True
                gate_num = 0
                # gate_check = jumps_left + 1
                # with open("pathlog.txt", "a") as log_file:
                #     log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- gate_check = {gate_check}\n")
                if gate in check_dict:
                    with open("pathlog.txt", "a") as log_file:
                        log_file.write(f"+++ ----- {gate} | {get_sys_name(gate)} found in check_dict |")
                    gate_num = check_dict[gate]
                    with open("pathlog.txt", "a") as log_file:
                        log_file.write(
                            f"gate_num set to {gate_num} | ")
                else:
                    with open("pathlog.txt", "a") as log_file:
                        log_file.write(f"+!+ ----- {gate} not found in check_dict |")

                if gate_num != 0 and query_id > gate_num -1:
                    gate_check = False

                with open("pathlog.txt", "a") as log_file:
                    log_file.write(f"gate_check set to {gate_check}\n")

                # if query_id > gate_check:
                #     with open("pathlog.txt", "a") as log_file:
                #         log_file.write(f"+|+{gate} rejected, {query_id} > {gate_check}\n")

                if gate != from_id and gate_check:

                    sys_gen = True

                    # Create new system from ID
                    new_system = System(get_sys_name(gate))
                    with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}-\n"
                          f"+------- Created New System: {new_system.system_id}|{new_system.name} -|- "
                          f"Stargates: {new_system.stargates}\n~|~ PASSING QUERY\n")

                    # Call this function recursively in newly created system
                    query_result = new_system.query_path(jumps_left - 1, goal, self.system_id, query_id)

                    # If goal was found anywhere in the recursive branch
                    if query_result != False:

                        # insert own ID into the path being handed back
                        query_result.insert(0, self.system_id)
                        with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- Returning {query_result} (NOT FALSE)\n")

                        # hand down path to goal
                        return query_result

            if not sys_gen:
                with open("pathlog.txt", "a") as log_file: log_file.write(
                    f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- Returning False - No Systems Genned\n")

                return False

            # Collapse back after failure to find goal on own branch
            with open("pathlog.txt", "a") as log_file: log_file.write(f"{query_id}:{query_tracker} -{self.system_id}|{self.name}- Returning {query_result}\n")
            check_dict[self.system_id] = query_id
            return query_result



    def update_score(self, current_system):
        pass

    def save_dump(self):
        return self.name


class Player:

    def __init__(self, system, goal=None):
        self.system = system
        self.paths = {}
        self.goal = goal

    # Find a path from current system to target system
    def make_path(self, goal, jumps):
        if jumps == 0:
            print("BAD JUMP ERROR")
            return
        global log_file
        with open("pathlog.txt", "a") as log_file:
            log_file.write(f"\n\nNumber of JUMPS = {jumps}\n\n")

        # Reset global tracker
        global query_tracker
        query_tracker = 0

        # Get ID for goal
        goal_id = get_sys_id(goal)

        # If path already exists for this system, return
        # ++++ DOES NOT WORK - MAY BREAK CODE IF IT DID, LOL ++++
        if goal_id in self.paths:
            return

        # Initialize check_dict
        global check_dict
        check_dict = {}

        # Create Starting system from current system
        start_system = System(self.system)

        # Start recursive operation, calling query path on starting system
        path = start_system.query_path(jumps, goal_id, start_system.system_id, query_id=0)

        # If path was not found, print statement
        if path == False:
            with open("pathlog.txt", "a") as log_file:
                log_file.write("Failed to find path")

        # Update paths dict with new path
        else:
            self.paths[goal] = path
            return

    # Update jumps in agents or missions
    def update_jumps(self, unit_dict):

        # Get ID for current system
        print(f"Player System: {self.system}, Player_sys_id: {get_sys_id(self.system)}")
        player_sys_id = get_sys_id(self.system)

        print(unit_dict)

        for unit in unit_dict:
            # Get name and ID for current mission or agent system
            unit_sys = unit_dict[unit].system
            unit_sys_id = get_sys_id(unit_sys)
            print(f"Check System: {unit_sys_id}\nCheck path: {self.paths[self.goal]}")
            # If system's ID is not in the path to the current goal, increase jumps by 1
            if unit_sys_id not in self.paths[self.goal]:
                unit_dict[unit].jumps += 1

            # If it IS in the path, decrease the jumps by the number of steps along the path it is
            else:
                unit_dict[unit].jumps -= 1

    def get_next_jump(self, agents, missions):
        # need to find clusters and prioritize cluster systems
        #   Find lists of tuple: (jumps between, system A, system B)
        #   Countup existing paths to get jump limit for path calculations
        #   Compare each system in path
        # 2 lists of all destinations
        # 1 list of tuples
        # 1 working system
        # do all work with systemIDs

        # List to iterate through
        find_list = []

        # List to compare to
        compare_list = []

        # Master List to buid
        master_list = []

        # populate both find and compare lists with all relevant goals
        for agent in agents:
            # Check to see if Agent System is a goal
            if agents[agent].status == "waiting":
                agent_sys = agents[agent].system
                agent_id = get_sys_id(agent_sys)
                find_list.append((agent_sys, agent_id))
                compare_list.append((agent_sys, agent_id))
        for mission in missions:
            mission_sys = missions[mission].system
            mission_id = get_sys_id(mission_sys)
            find_list.append((mission_sys, mission_id))
            compare_list.append((mission_sys, mission_id))

        # The Important Stuff
        # for system in find_list:
        #     if system in compare_list:
        #         del compare_list[compare_list.index(system)]
        #     for comp_sys in compare_list:
        #         sys_path = self.paths[system[0]]
        #         comp_path = self.paths[comp_sys[0]]

        # need to find shortest jumps
        # return list of jumps in order, destination systems marked !!system!!
        sort_list = []
        for system in find_list:
            path_length = len(self.paths[system[0]]) - 1
            print(self.paths)
            sort_list.append((path_length, system[0], get_sys_name(self.paths[system[0]][1])))
        sort_list.sort()
        return sort_list[0]

    def update_system(self, new_system):
        print(f"Player System changed from {self.system} to {new_system}")
        self.system = new_system

    def dump_path_names(self):
        for system in self.paths:
            temp_list = []
            for sys_id in self.paths[system]:
                temp_list.append(get_sys_name(sys_id))
            print(temp_list)