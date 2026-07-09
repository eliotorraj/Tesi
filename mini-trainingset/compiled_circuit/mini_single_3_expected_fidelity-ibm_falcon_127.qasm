OPENQASM 2.0;
include "qelib1.inc";
qreg q[127];
rz(-pi) q[0];
sx q[0];
rz(pi/2) q[0];
x q[1];
rz(0.25) q[2];
