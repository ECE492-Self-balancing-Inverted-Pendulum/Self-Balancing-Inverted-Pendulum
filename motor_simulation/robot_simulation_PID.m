%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%Run this code here before running the simulation
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Clear existing models and command window
close_system('all', 0);
clc;

% Define system parameters
m_b = 1;    % Body mass (kg)
m_w = 0.2;  % Wheel mass (kg)
r = 0.09;   % Wheel radius (m)
l = 0.2;    % Height of center of mass (m)
g = 9.81;   % Gravity (m/s^2)
I = m_b * l^2; % Moment of inertia of body
I_w = 0.5 * m_w * r^2; % Wheel inertia

% State-space matrices
A = [0 1 0 0; (m_b * g * l)/I 0 0 0; 0 0 0 1; 0 0 0 0];
B = [0; 1/I; 0; r/I_w];
C = [1 0 0 0]; % Output only theta for PID control
D = 0;

% Create state-space model
plant = ss(A, B, C, D);

% Set simulation parameters
set_param(modelName, 'Solver', 'ode45', 'StopTime', '10', 'MaxStep', '0.001');

% Open the model
open_system(modelName);