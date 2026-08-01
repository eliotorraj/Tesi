OPENQASM 2.0;
include "qelib1.inc";
qreg q[127];
creg c[1];
x q[4];
cx q[4],q[15];
barrier q[15],q[4];
measure q[15] -> c[0];
