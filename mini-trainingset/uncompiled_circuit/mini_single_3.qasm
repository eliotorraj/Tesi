OPENQASM 2.0;
include "qelib1.inc";

qreg q[3];

h q[0];
x q[1];
rz(0.25) q[2];
sx q[0];
