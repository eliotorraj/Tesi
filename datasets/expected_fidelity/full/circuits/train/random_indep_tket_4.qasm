// Benchmark was created by MQT Bench on 2023-06-29
// For more information about MQT Bench, please visit https://www.cda.cit.tum.de/mqtbench/
// MQT Bench version: v1.0.0
// TKET version: 1.16.0

OPENQASM 2.0;
include "qelib1.inc";

qreg q[4];
creg meas[4];
u2(0.5*pi,1.7718392080410132*pi) q[0];
u1(1.5256092328731303*pi) q[1];
u2(0.0*pi,0.0*pi) q[2];
u2(1.3780729595622632*pi,1.6834954486245568*pi) q[3];
cx q[2],q[1];
ry(3.85071787691798*pi) q[1];
ry(3.85071787691798*pi) q[2];
cx q[2],q[1];
u2(0.25*pi,1.4743907671268706*pi) q[1];
u2(1.0*pi,1.0*pi) q[2];
cx q[2],q[1];
tdg q[1];
cx q[3],q[1];
t q[1];
h q[3];
cx q[2],q[1];
u2(0.0*pi,0.75*pi) q[1];
u3(1.0*pi,1.8967602500943939*pi,0.1032397499056062*pi) q[2];
ccx q[0],q[1],q[3];
u2(1.5*pi,0.43966073641264375*pi) q[0];
u3(0.0004489612074336284*pi,0.5*pi,0.852424223176459*pi) q[1];
u3(1.0*pi,0.5*pi,1.5*pi) q[3];
cx q[3],q[2];
ry(3.7738855663254727*pi) q[2];
ry(0.22611443367452747*pi) q[3];
cx q[3],q[2];
u2(1.3572975470162845*pi,1.5153296407330008*pi) q[2];
u2(1.0*pi,0.5*pi) q[3];
rzz(0.6675289134386755*pi) q[0],q[3];
rx(3.5*pi) q[0];
u3(0.25*pi,1.5*pi,1.0*pi) q[3];
crx(0.4978418751829938*pi) q[2],q[0];
u1(0.7971374765446473*pi) q[0];
cx q[2],q[3];
cx q[1],q[0];
h q[3];
ry(3.660484424765582*pi) q[0];
ry(3.660484424765582*pi) q[1];
cu1(0.5*pi) q[2],q[3];
cx q[1],q[0];
u1(1.5344820340774552*pi) q[3];
u1(1.2028625234553527*pi) q[0];
u2(1.0*pi,1.0*pi) q[1];
cu3(1.2676501147241983*pi,0.22928871795830214*pi,0.4661809484628782*pi) q[3],q[0];
cx q[1],q[2];
cx q[2],q[1];
barrier q[0],q[1],q[2],q[3];
measure q[0] -> meas[0];
measure q[1] -> meas[1];
measure q[2] -> meas[2];
measure q[3] -> meas[3];
