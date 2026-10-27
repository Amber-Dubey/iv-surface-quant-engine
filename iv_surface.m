% =========================================================================
% Implied Volatility Surface & Multivariable Gradient Engine
% Built using primitive commands: meshgrid, gradient, surf, plot, erf
% =========================================================================
clear; clc; close all;

% 1. Parameter Initialization (Dynamic vs Standalone Fallback)
if exist('params.m', 'file')
    run('params.m'); % Loaded dynamically when called via Python UI (S, r, K, T, market_prices)
else
    % Standalone Default Environment Parameters (Synthetic Fallback)
    S = 100.0;           % Spot Price
    r = 0.05;            % Risk-Free Rate
    
    % PRIMITIVE FUNCTION: meshgrid (Constructing the 2D Domain Matrix)
    strikes = linspace(80, 120, 30);
    maturities = linspace(0.1, 2.0, 25);
    [K, T] = meshgrid(strikes, maturities);
    
    % Generate synthetic market option prices mirroring a volatility skew
    true_iv = 0.20 + 0.05 * (K/S - 1).^2 + 0.02 ./ T;
    d1_synth = (log(S ./ K) + (r + 0.5 * true_iv.^2) .* T) ./ (true_iv .* sqrt(T));
    d2_synth = d1_synth - true_iv .* sqrt(T);
    
    % Primitive Cumulative Normal Distribution using error function (erf)
    N_d1 = 0.5 * (1 + erf(d1_synth / sqrt(2)));
    N_d2 = 0.5 * (1 + erf(d2_synth / sqrt(2)));
    market_prices = S * N_d1 - K .* exp(-r * T) .* N_d2;
end

% 2. Newton-Raphson Numerical Root-Finding Loop
% Uses Multivariable Calculus: Partial Derivative Vega (dC / dSigma)
IV = zeros(size(market_prices));

for i = 1:size(market_prices, 1)
    for j = 1:size(market_prices, 2)
        k_val = K(i,j);
        t_val = T(i,j);
        mkt_price = market_prices(i,j);
        
        if isnan(mkt_price) || mkt_price <= 0
            continue;
        end
        
        sigma = 0.20; % Initial volatility guess
        for iter = 1:50
            d1 = (log(S / k_val) + (r + 0.5 * sigma^2) * t_val) / (sigma * sqrt(t_val));
            d2 = d1 - sigma * sqrt(t_val);
            
            N_d1 = 0.5 * (1 + erf(d1 / sqrt(2)));
            N_d2 = 0.5 * (1 + erf(d2 / sqrt(2)));
            
            bs_price = S * N_d1 - k_val * exp(-r * t_val) * N_d2;
            diff = bs_price - mkt_price;
            
            if abs(diff) < 1e-6
                break;
            end
            
            % Partial Derivative: Vega (Sensitivity of Price to Volatility)
            % nu = dC / dSigma = S * sqrt(T) * n(d1)
            n_d1 = (1 / sqrt(2 * pi)) * exp(-0.5 * d1^2);
            vega = S * sqrt(t_val) * n_d1;
            
            if abs(vega) < 1e-12
                break;
            end
            
            sigma = sigma - diff / vega;
            if sigma <= 0
                sigma = 1e-4;
            end
        end
        IV(i,j) = sigma;
    end
end

% 3. MULTIVARIABLE CALCULUS: Surface Gradients
% PRIMITIVE FUNCTION: gradient 
% Computes numerical partial derivatives [dIV/dK, dIV/dT] across the 2D surface matrix
[dIV_dK, dIV_dT] = gradient(IV);

% 4. Output Execution Mode
if exist('params.m', 'file')
    % Save matrices for Python / Streamlit consumption
    save('-v7', 'results.mat', 'K', 'T', 'IV', 'market_prices', 'dIV_dK', 'dIV_dT');
else
    % =====================================================================
    % Native Standalone GNU Octave Mode: 3 Separate Independent Windows
    % =====================================================================
    
    % --- WINDOW 1: 3D Implied Volatility Surface ---
    figure('Name', 'Figure 1: 3D Implied Volatility Surface', 'Color', 'white');
    surf(K, T, IV, 'FaceColor', 'interp', 'EdgeColor', 'none');
    colormap(jet);
    colorbar;
    camlight; lighting gouraud;
    title('3D Implied Volatility Surface (Black-Scholes Inversion)');
    xlabel('Strike Price (K)');
    ylabel('Time to Maturity (T)');
    zlabel('Implied Volatility (\sigma)');
    grid on;
    
    % --- WINDOW 2: 2D Volatility Smile (Strike Slice) ---
    figure('Name', 'Figure 2: 2D Volatility Smile Cross-Section', 'Color', 'white');
    mid_row = round(size(K, 1) / 2);
    plot(K(mid_row, :), IV(mid_row, :), '-ro', 'LineWidth', 2, 'MarkerFaceColor', 'r');
    grid on;
    title(['2D Volatility Smile (Slice at Maturity T = ', num2str(T(mid_row, 1), '%.2f'), ')']);
    xlabel('Strike Price (K)');
    ylabel('Implied Volatility (\sigma)');
    
    % --- WINDOW 3: 2D Term Structure (Maturity Slice) ---
    figure('Name', 'Figure 3: 2D Term Structure Cross-Section', 'Color', 'white');
    mid_col = round(size(K, 2) / 2);
    plot(T(:, mid_col), IV(:, mid_col), '-bs', 'LineWidth', 2, 'MarkerFaceColor', 'b');
    grid on;
    title(['2D Term Structure (Slice at Strike K = ', num2str(K(1, mid_col), '%.2f'), ')']);
    xlabel('Time to Maturity (T)');
    ylabel('Implied Volatility (\sigma)');
end