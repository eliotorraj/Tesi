OPENQASM 2.0;
include "qelib1.inc";

qreg q[4];

h q[0];
h q[2];
cx q[0], q[1];
cx q[2], q[3];
rz(0.125) q[1];
rz(0.375) q[3];
