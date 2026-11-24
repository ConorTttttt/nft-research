"""Loopback research service adding verified grant installation to Phase 2."""

import socketserver
import subprocess
import sys
from pathlib import Path
from grant import Profile, raw, require
from lab import Lab
from witness import Handler, Store


def genesis(parent):
    return int.from_bytes(raw(parent)) < 16384


class GrantStore(Store):
    def __init__(self, directory, profile):
        super().__init__(directory, False)
        require(self.config["anchor"] == profile.anchor(self.config), "policy mismatch")
        self.profile = profile

    def run(self, request):
        op = request["op"]
        if op == "install_grant":
            child, owner = self.profile.exercise(
                self.config, request["parent"], request["proof"], request["terminal"]
            )
            with self.db:
                self.db.execute(
                    "INSERT OR IGNORE INTO rights VALUES(?,?)", (child, owner)
                )
                require(self.owner(child) == owner, "inconsistent installed controller")
            return child
        if op in ("install", "reset") and genesis(request["parent"]):
            raise ValueError("lab genesis requires a terminal grant")
        if op == "vote":
            proposal = request["p"]
            moves = proposal["moves"]
            if any(genesis(parent) for parent, _ in moves):
                require(
                    len(moves) == 1
                    and proposal["mode"] == "flat"
                    and moves[0][1] == self.config["users"][1],
                    "genesis grant terms",
                )
        return super().run(request)


class GrantLab(Lab):
    def __init__(self, profile):
        self.profile = profile
        super().__init__(7, 5, 2, anchor_for=profile.anchor)

    def start(self, i):
        proc = subprocess.Popen(
            [
                sys.executable,
                __file__,
                str(self.path / str(i)),
                self.profile.issuer,
                self.profile.network.hex(),
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        self.procs[i] = proc
        self.ports[i] = int(proc.stdout.readline())


if __name__ == "__main__":
    with socketserver.TCPServer(("127.0.0.1", 0), Handler) as server:
        server.store = GrantStore(
            Path(sys.argv[1]), Profile(sys.argv[2], bytes.fromhex(sys.argv[3]))
        )
        print(server.server_address[1], flush=True)
        server.serve_forever()
