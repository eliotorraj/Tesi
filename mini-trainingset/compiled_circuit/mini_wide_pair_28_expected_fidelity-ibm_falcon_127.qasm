OPENQASM 2.0;
include "qelib1.inc";
qreg q[127];
rz(pi/2) q[15];
sx q[15];
rz(pi/2) q[15];
cx q[15],q[4];
rz(0.5) q[62];
