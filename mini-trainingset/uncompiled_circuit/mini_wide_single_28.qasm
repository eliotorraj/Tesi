OPENQASM 2.0;
include "qelib1.inc";

qreg q[28];

h q[0];
x q[13];
rz(0.25) q[27];
