import os

if __name__ == '__main__':
    print(', '.join(["date", "contract_name", "loc", "num_walks", "num_of_cfg_nodes", "exec_time"]))

    for output in os.listdir('output/'):
        with open(os.path.join('output/', output, 'output.loc')) as f:
            loc = f.readline()

        with open(os.path.join('output/', output, 'out.log')) as f:
            num_walks = 0
            num_of_cfg_nodes = -1
            exec_time = None
            contract_name = None

            for line in f.readlines():
                if 'new path' in line:
                    num_walks += 1

                if line.startswith("[info] Contract Name: "):
                    contract_name = line.removeprefix("[info] Contract Name: ").removesuffix("\n")
                if line.startswith("[debug] #NUM_OF_CFG_NODES: "):
                    num_of_cfg_nodes = line.removeprefix("[debug] #NUM_OF_CFG_NODES: ").removesuffix("\n")
                if line.startswith("[info] Exec Time: "):
                    exec_time = str(float(line.removeprefix("[info] Exec Time: ").removesuffix('s\n')))

        print(', '.join([output, contract_name, loc, str(num_walks), num_of_cfg_nodes, exec_time]))
