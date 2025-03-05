% Clear existing models and command window
close_system('all', 0);
clc;

% Create a new Simulink model
modelName = 'SelfBalancingRobotModel';
new_system(modelName);
open_system(modelName);

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

% Add blocks to the model
% 1. State-Space Block
add_block('simulink/Continuous/State-Space', [modelName '/StateSpace']);
set_param([modelName '/StateSpace'], ...
    'A', mat2str(A), ...
    'B', mat2str(B), ...
    'C', mat2str(eye(4)), ... % Output all states for Scopes
    'D', mat2str(zeros(4, 1)), ...
    'InitialCondition', '[0.017; 0; 0; 0]', ... % Initial angle = 1 degree (0.017 rad)
    'Position', [300 100 450 200]);

% 2. PID Controller Block
add_block('simulink/Continuous/PID Controller', [modelName '/PID']);
set_param([modelName '/PID'], ...
    'P', '50', ... % Initial guess
    'I', '1', ...
    'D', '10', ...
    'Position', [150 150 250 250]);

% 3. Sum Block (for error calculation)
add_block('simulink/Math Operations/Sum', [modelName '/Sum']);
set_param([modelName '/Sum'], ...
    'Inputs', '+-', ...
    'Position', [150 100 200 150]);

% 4. Constant Block (Reference angle = 0)
add_block('simulink/Sources/Constant', [modelName '/Reference']);
set_param([modelName '/Reference'], ...
    'Value', '0', ...
    'Position', [50 100 100 150]);

% 5. Scope Blocks for theta, theta_dot, x, x_dot
add_block('simulink/Sinks/Scope', [modelName '/Scope_Theta'], 'Position', [500 50 550 150]);
add_block('simulink/Sinks/Scope', [modelName '/Scope_ThetaDot'], 'Position', [500 200 550 300]);
add_block('simulink/Sinks/Scope', [modelName '/Scope_X'], 'Position', [600 50 650 150]);
add_block('simulink/Sinks/Scope', [modelName '/Scope_XDot'], 'Position', [600 200 650 300]);

% 6. Demux Block (to separate all states)
add_block('simulink/Signal Routing/Demux', [modelName '/Demux']);
set_param([modelName '/Demux'], ...
    'Outputs', '4', ... % Split into 4 signals: theta, theta_dot, x, x_dot
    'Position', [450 100 500 150]);

% 7. Noise Block (Band-Limited White Noise)
add_block('simulink/Sources/Band-Limited White Noise', [modelName '/Noise']);
set_param([modelName '/Noise'], ...
    'Noise power', '0.001', ... % Reduced noise power
    'Sample time', '0.01', ...
    'Seed', '23341', ...
    'Position', [300 300 350 350]);

% 8. Sum Block for adding noise to feedback
add_block('simulink/Math Operations/Sum', [modelName '/Sum_Noise']);
set_param([modelName '/Sum_Noise'], ...
    'Inputs', '+-', ...
    'Position', [250 100 300 150]);

% Connect the blocks
add_line(modelName, 'Reference/1', 'Sum/1', 'autorouting', 'on');          % Reference to Sum
add_line(modelName, 'Sum_Noise/1', 'Sum/2', 'autorouting', 'on');         % Noisy theta feedback to Sum
add_line(modelName, 'Sum/1', 'PID/1', 'autorouting', 'on');              % Error to PID
add_line(modelName, 'PID/1', 'StateSpace/1', 'autorouting', 'on');        % PID output to State-Space
add_line(modelName, 'StateSpace/1', 'Demux/1', 'autorouting', 'on');      % State-Space output to Demux
add_line(modelName, 'Demux/1', 'Scope_Theta/1', 'autorouting', 'on');     % Theta to Scope_Theta
add_line(modelName, 'Demux/2', 'Scope_ThetaDot/1', 'autorouting', 'on');  % Theta_dot to Scope_ThetaDot
add_line(modelName, 'Demux/3', 'Scope_X/1', 'autorouting', 'on');         % X to Scope_X
add_line(modelName, 'Demux/4', 'Scope_XDot/1', 'autorouting', 'on');      % X_dot to Scope_XDot
add_line(modelName, 'Demux/1', 'Sum_Noise/1', 'autorouting', 'on');       % Theta feedback to Sum_Noise
add_line(modelName, 'Noise/1', 'Sum_Noise/2', 'autorouting', 'on');       % Noise to Sum_Noise

% Set simulation parameters
set_param(modelName, 'Solver', 'ode45', 'StopTime', '10', 'MaxStep', '0.001');

% Auto-tune PID using PID Tuner
% Open PID Tuner for the PID block
pidBlock = [modelName '/PID'];
pidTunerCmd = ['pidTuner(''' pidBlock ''', ''system'', ''' modelName ''')'];
eval(pidTunerCmd);

% Note: The PID Tuner GUI will open, and you need to manually accept the tuned gains
% or use the following to extract gains programmatically after tuning (optional)
% [Kp_new, Ki_new, Kd_new] = getBlockParameter(pidBlock, {'P', 'I', 'D'});
% set_param(pidBlock, 'P', num2str(Kp_new), 'I', num2str(Ki_new), 'D', num2str(Kd_new));

% Save and display the model
save_system(modelName);
disp(['Simulink model "' modelName '" has been created and saved.']);

% Open the model
open_system(modelName);