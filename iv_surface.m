% =========================================================================
% Quantitative Implied Volatility Surface & Gradient Engine
% =========================================================================
clear; clc; close all;

disp('>> Loading Market Data from absolute path...');
load('C:/Users/ishit/Documents/GitHub/iv-surface-quant-engine/aapl_real_data.mat'); 

% Extract dynamic ticker name
if exist('ticker_name', 'var')
    t_str = char(ticker_name);
else
    t_str = 'AAPL';
end

disp(['>> Ticker: ', t_str, ' | Spot Price Loaded: $', num2str(S, '%.2f')]);
disp('>> Executing Newton-Raphson Numerical Root-Finding...');

IV = zeros(size(market_prices));

for i = 1:size(market_prices, 1)
    for j = 1:size(market_prices, 2)
        k_val = K(i,j);
        t_val = T(i,j);
        mkt_price = market_prices(i,j);
        
        if isnan(mkt_price) || mkt_price <= 0
            continue;
        end
        
        sigma = 0.25; 
        for iter = 1:50
            bs_d1 = (log(S / k_val) + (r + 0.5 * sigma^2) * t_val) / (sigma * sqrt(t_val));
            bs_d2 = bs_d1 - sigma * sqrt(t_val);
            
            bs_N_d1 = 0.5 * (1 + erf(bs_d1 / sqrt(2)));
            bs_N_d2 = 0.5 * (1 + erf(bs_d2 / sqrt(2)));
            
            bs_price = S * bs_N_d1 - k_val * exp(-r * t_val) * bs_N_d2;
            diff = bs_price - mkt_price;
            
            if abs(diff) < 1e-6
                break;
            end
            
            n_d1 = (1 / sqrt(2 * pi)) * exp(-0.5 * bs_d1^2);
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

IV(isnan(IV) | IV <= 0) = 0.20;
IV(IV > 1.50) = 1.50; 
IV(IV < 0.05) = 0.05;

[dIV_dK, dIV_dT] = gradient(IV);

disp('>> Rendering 3 Independent Native Octave Visual Windows...');

% --- WINDOW 1: 3D Implied Volatility Surface ---
figure(1);
clf;
set(gcf, 'Name', ['Figure 1: ', t_str, ' 3D Implied Volatility Surface'], 'Color', 'white');
surf(K, T, IV, 'FaceColor', 'interp', 'EdgeColor', 'none');
colormap(jet);
colorbar;
camlight; lighting gouraud;
title([t_str, ' 3D Implied Volatility Surface (Black-Scholes Inversion)']);
xlabel('Strike Price (K)');
ylabel('Time to Maturity (T)');
zlabel('Implied Volatility (\sigma)');
grid on;
drawnow; 

% --- WINDOW 2: 2D Volatility Smile Cross-Section ---
figure(2);
clf;
set(gcf, 'Name', ['Figure 2: ', t_str, ' 2D Volatility Smile'], 'Color', 'white');
mid_row = round(size(K, 1) / 2);
plot(K(mid_row, :), IV(mid_row, :), '-ro', 'LineWidth', 2.5, 'MarkerFaceColor', 'r');
grid on;
title([t_str, ' 2D Volatility Smile (Strike Slice at T = ', num2str(T(mid_row, 1), '%.3f'), ' yrs)']);
xlabel('Strike Price (K)');
ylabel('Implied Volatility (\sigma)');
drawnow; 

% --- WINDOW 3: 2D Term Structure Cross-Section ---
figure(3);
clf;
set(gcf, 'Name', ['Figure 3: ', t_str, ' 2D Term Structure'], 'Color', 'white');
mid_col = round(size(K, 2) / 2);
plot(T(:, mid_col), IV(:, mid_col), '-bs', 'LineWidth', 2.5, 'MarkerFaceColor', 'b');
grid on;
title([t_str, ' 2D Term Structure (Maturity Slice at K = $', num2str(K(1, mid_col), '%.1f'), ')']);
xlabel('Time to Maturity (T in Years)');
ylabel('Implied Volatility (\sigma)');
drawnow; 

% --- QUANTITATIVE SUMMARY REPORT ---
disp('--------------------------------------------------');
fprintf('          %s IV SURFACE QUANTITATIVE REPORT\n', t_str);
disp('--------------------------------------------------');
[~, atm_col_idx] = min(abs(K(1, :) - S));
atm_row_idx = round(size(T, 1) / 2);
atm_iv = IV(atm_row_idx, atm_col_idx);
min_iv = min(IV(:));
max_iv = max(IV(:));
otm_put_iv = IV(atm_row_idx, 1);
skew_spread = otm_put_iv - atm_iv;

fprintf('- Spot Price (S)          : $%.2f\n', S);
fprintf('- At-The-Money (ATM) IV   : %.2f%%\n', atm_iv * 100);
fprintf('- Minimum Surface IV      : %.2f%%\n', min_iv * 100);
fprintf('- Maximum Surface IV      : %.2f%%\n', max_iv * 100);
fprintf('- Volatility Skew Spread  : %.4f (OTM Put vs ATM)\n', skew_spread);
fprintf('- Grid Resolution         : %d Strikes x %d Maturities\n', size(K, 2), size(K, 1));
disp('--------------------------------------------------');

% Save report to text file for Python GUI to read cleanly
report_file = fopen('report.txt', 'w');
fprintf(report_file, '--------------------------------------------------\n');
fprintf(report_file, '          %s IV SURFACE QUANTITATIVE REPORT\n', t_str);
fprintf(report_file, '--------------------------------------------------\n');
fprintf(report_file, '- Spot Price (S)          : $%.2f\n', S);
fprintf(report_file, '- At-The-Money (ATM) IV   : %.2f%%\n', atm_iv * 100);
fprintf(report_file, '- Minimum Surface IV      : %.2f%%\n', min_iv * 100);
fprintf(report_file, '- Maximum Surface IV      : %.2f%%\n', max_iv * 100);
fprintf(report_file, '- Volatility Skew Spread  : %.4f (OTM Put vs ATM)\n', skew_spread);
fprintf(report_file, '- Grid Resolution         : %d Strikes x %d Maturities\n', size(K, 2), size(K, 1));
fprintf(report_file, '--------------------------------------------------\n');
fclose(report_file);