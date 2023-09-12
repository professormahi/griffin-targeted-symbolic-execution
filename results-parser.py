import os

if __name__ == '__main__':
    print(', '.join(["date", "contract_name", "loc", "num_walks", "num_of_cfg_nodes", "exec_time", "heuristic"]))

    for output in os.listdir('output/'):
        try:
            with open(os.path.join('output/', output, 'output.loc')) as f:
                loc = f.readline()
        except FileNotFoundError:
            continue

        with open(os.path.join('output/', output, 'out.log')) as f:
            num_walks = 0
            num_of_cfg_nodes = -1
            exec_time = None
            contract_name = None
            heuristic = None

            for line in f.readlines():
                if 'new path' in line:
                    num_walks += 1

                if line.startswith("[info] Contract Name: "):
                    contract_name = line.removeprefix("[info] Contract Name: ").removesuffix("\n")
                if line.startswith("[debug] #NUM_OF_CFG_NODES: "):
                    num_of_cfg_nodes = line.removeprefix("[debug] #NUM_OF_CFG_NODES: ").removesuffix("\n")
                if line.startswith("[info] Exec Time: "):
                    exec_time = str(float(line.removeprefix("[info] Exec Time: ").removesuffix('s\n')))
                if line.startswith("[debug] Heuristic "):
                    heuristic = line.removeprefix("[debug] Heuristic ").removesuffix('\n')

            if exec_time is None:
                continue

        print(', '.join([output, contract_name, loc, str(num_walks), num_of_cfg_nodes, exec_time, heuristic]))
