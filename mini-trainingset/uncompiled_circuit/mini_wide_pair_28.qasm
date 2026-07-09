OPENQASM 2.0;
include "qelib1.inc";

qreg q[28];

h q[0];
cx q[0], q[27];
rz(0.5) q[14];
