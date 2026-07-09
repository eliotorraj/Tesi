OPENQASM 2.0;
include "qelib1.inc";
qreg q[56];
ry(pi/2) q[0];
rx(pi) q[0];
rx(pi) q[13];
rz(0.25) q[27];
