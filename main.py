import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Normal
import matplotlib.pyplot as plt
import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np
import math

def plot_comprehensive_stats_with_csv(trainer, episode, successes, max_altitudes, max_velocities, final_rewards,
                                      csv_file_path=None):
    """Plot comprehensive statistics including training progress and test results with optional CSV comparison"""

    # Load CSV data if provided
    csv_data = None
    if csv_file_path:
        try:
            csv_data = pd.read_csv(csv_file_path)
            print(f"✅ Loaded CSV data from {csv_file_path} with {len(csv_data)} rows")
            print(f"📊 CSV columns: {list(csv_data.columns)}")  # Debug: show available columns
        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            csv_data = None

    # Create a comprehensive figure with multiple subplots
    fig = plt.figure(figsize=(20, 16))

    # 1. Training Progress - Rewards
    plt.subplot(3, 4, 1)
    plt.plot(trainer.episode_rewards, 'b-', alpha=0.7, linewidth=1, label='AI Training')

    # Add CSV reward data if available
    if csv_data is not None and 'reward' in csv_data.columns:
        plt.plot(csv_data['reward'], 'r-', alpha=0.7, linewidth=1, label='CSV Data')
        plt.legend()

    plt.title('Training: Episode Rewards')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.grid(True, alpha=0.3)

    # 2. Training Progress - Max Altitudes
    plt.subplot(3, 4, 2)
    altitudes_km = [alt / 1000 for alt in trainer.max_altitudes]
    plt.plot(altitudes_km, 'g-', alpha=0.7, linewidth=1, label='AI Altitude')

    # Add CSV altitude data if available
    if csv_data is not None and 'altitude' in csv_data.columns:
        csv_altitudes_km = csv_data['altitude'] / 1000 if max(csv_data['altitude']) > 1000 else csv_data['altitude']
        plt.plot(csv_altitudes_km, 'orange', alpha=0.7, linewidth=1, label='CSV Altitude')

    plt.axhline(y=trainer.env.target_altitude / 1000, color='r', linestyle='--',
                label=f'Target: {trainer.env.target_altitude / 1000:.0f}km')
    plt.title('Training: Max Altitude Reached')
    plt.xlabel('Episode')
    plt.ylabel('Altitude (km)')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 3. Test Results - Altitude Distribution
    plt.subplot(3, 4, 3)
    if max_altitudes:
        test_altitudes_km = [alt / 1000 for alt in max_altitudes]
        plt.hist(test_altitudes_km, bins=10, alpha=0.7, color='green', edgecolor='black', label='AI Test Results')

        # Add CSV altitude distribution if available
        if csv_data is not None and 'altitude' in csv_data.columns:
            csv_altitudes = csv_data['altitude'] / 1000 if max(csv_data['altitude']) > 1000 else csv_data['altitude']
            plt.hist(csv_altitudes, bins=10, alpha=0.5, color='red', edgecolor='black', label='CSV Data')

        plt.axvline(x=trainer.env.target_altitude / 1000, color='r', linestyle='--',
                    label='Target Orbit')
        plt.xlabel('Maximum Altitude (km)')
        plt.ylabel('Frequency')
        plt.title(f'Test Results: Altitude Distribution\nSuccess Rate: {successes}/{len(max_altitudes)}')
        plt.legend()

    # 4. Test Results - Velocity Distribution
    plt.subplot(3, 4, 4)
    if max_velocities:
        plt.hist(max_velocities, bins=10, alpha=0.7, color='orange', edgecolor='black', label='AI Test Results')

        # Add CSV velocity distribution if available
        if csv_data is not None and 'velocity' in csv_data.columns:
            plt.hist(csv_data['velocity'], bins=10, alpha=0.5, color='purple', edgecolor='black', label='CSV Data')

        plt.axvline(x=trainer.env.orbital_velocity, color='r', linestyle='--',
                    label=f'Orbital: {trainer.env.orbital_velocity:.0f}m/s')
        plt.xlabel('Maximum Velocity (m/s)')
        plt.ylabel('Frequency')
        plt.title('Test Results: Velocity Distribution')
        plt.legend()

    # 5. Test Results - Reward Distribution
    plt.subplot(3, 4, 5)
    if final_rewards:
        plt.hist(final_rewards, bins=10, alpha=0.7, color='purple', edgecolor='black', label='AI Test Results')

        # Add CSV reward distribution if available
        if csv_data is not None and 'reward' in csv_data.columns:
            plt.hist(csv_data['reward'], bins=10, alpha=0.5, color='blue', edgecolor='black', label='CSV Data')
            plt.legend()

        plt.xlabel('Final Reward')
        plt.ylabel('Frequency')
        plt.title('Test Results: Reward Distribution')

    # 6. Success/Failure Breakdown
    plt.subplot(3, 4, 6)
    if max_altitudes:
        success_count = successes
        failure_count = len(max_altitudes) - success_count

        # Calculate CSV success rate if available
        csv_success_rate = None
        csv_success_count = 0
        csv_total = 0
        if csv_data is not None and 'success' in csv_data.columns:
            csv_success_count = csv_data['success'].sum()
            csv_total = len(csv_data)
            csv_success_rate = csv_success_count / csv_total * 100

        labels = ['AI Success', 'AI Failure']
        sizes = [success_count, failure_count]
        colors = ['#2ecc71', '#e74c3c']

        if csv_success_rate is not None:
            labels.extend([f'CSV Success ({csv_success_rate:.1f}%)'])
            sizes.extend([csv_success_count])
            colors.extend(['#3498db'])

        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Mission Success Rate Comparison')

    # 7. Recent Performance (last 100 episodes)
    plt.subplot(3, 4, 7)
    if len(trainer.episode_rewards) > 100:
        recent_rewards = trainer.episode_rewards[-100:]
        plt.plot(recent_rewards, 'b-', alpha=0.7, label='AI Recent')

        # Add recent CSV data if available
        if csv_data is not None and 'reward' in csv_data.columns:
            csv_recent = csv_data['reward'].tail(100) if len(csv_data) > 100 else csv_data['reward']
            plt.plot(csv_recent.values, 'r-', alpha=0.7, label='CSV Recent')
            plt.legend()

        plt.title('Recent 100 Episodes: Rewards')
        plt.xlabel('Episode (relative)')
        plt.ylabel('Reward')
        plt.grid(True, alpha=0.3)

    # 8. Altitude vs Velocity Scatter
    plt.subplot(3, 4, 8)
    if max_altitudes and max_velocities:
        plt.scatter([alt / 1000 for alt in max_altitudes], max_velocities, alpha=0.6,
                    c=final_rewards if final_rewards else 'blue', cmap='viridis', label='AI Tests')

        # Add CSV scatter data if available
        if csv_data is not None and 'altitude' in csv_data.columns and 'velocity' in csv_data.columns:
            csv_altitudes = csv_data['altitude'] / 1000 if max(csv_data['altitude']) > 1000 else csv_data['altitude']
            plt.scatter(csv_altitudes, csv_data['velocity'], alpha=0.6,
                        c='red', marker='x', s=50, label='CSV Data')

        plt.axhline(y=trainer.env.orbital_velocity, color='r', linestyle='--',
                    label='Orbital Velocity')
        plt.axvline(x=trainer.env.target_altitude / 1000, color='r', linestyle='--',
                    label='Target Altitude')
        plt.xlabel('Max Altitude (km)')
        plt.ylabel('Max Velocity (m/s)')
        plt.title('Altitude vs Velocity Comparison')
        plt.legend()
        if final_rewards:
            plt.colorbar(label='AI Final Reward')

    # 9. Moving Average Rewards
    plt.subplot(3, 4, 9)
    if len(trainer.episode_rewards) > 50:
        window = min(50, len(trainer.episode_rewards))
        moving_avg = np.convolve(trainer.episode_rewards, np.ones(window) / window, mode='valid')
        plt.plot(moving_avg, 'r-', linewidth=2, label=f'AI {window}-episode MA')

        # Add CSV moving average if available
        if csv_data is not None and 'reward' in csv_data.columns:
            csv_window = min(50, len(csv_data))
            csv_ma = csv_data['reward'].rolling(window=csv_window).mean().dropna()
            plt.plot(csv_ma.values, 'orange', linewidth=2, label=f'CSV {csv_window}-episode MA')
            plt.legend()

        plt.title('Reward Moving Average Comparison')
        plt.xlabel('Episode')
        plt.ylabel('Average Reward')
        plt.grid(True, alpha=0.3)

    # 10. Training Progress Over Time
    plt.subplot(3, 4, 10)
    episodes = range(len(trainer.episode_rewards))
    plt.scatter(episodes, trainer.episode_rewards, alpha=0.3, s=1, color='blue', label='AI Raw rewards')

    # Add CSV data points if available
    if csv_data is not None and 'reward' in csv_data.columns:
        csv_episodes = range(len(csv_data))
        plt.scatter(csv_episodes, csv_data['reward'], alpha=0.3, s=1, color='red', label='CSV Raw rewards')
        plt.legend()

    # Add trend line for AI
    if len(episodes) > 10:
        z = np.polyfit(episodes, trainer.episode_rewards, 1)
        p = np.poly1d(z)
        plt.plot(episodes, p(episodes), "b--", alpha=0.8, linewidth=2,
                 label=f'AI Trend (slope: {z[0]:.4f})')

    # Add trend line for CSV if available
    if csv_data is not None and 'reward' in csv_data.columns and len(csv_data) > 10:
        csv_episodes = range(len(csv_data))
        z_csv = np.polyfit(csv_episodes, csv_data['reward'], 1)
        p_csv = np.poly1d(z_csv)
        plt.plot(csv_episodes, p_csv(csv_episodes), "r--", alpha=0.8, linewidth=2,
                 label=f'CSV Trend (slope: {z_csv[0]:.4f})')
        plt.legend()

    plt.title('Reward Trend Over Training')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.grid(True, alpha=0.3)

    # 11. Performance Metrics Summary
    plt.subplot(3, 4, 11)

    # Initialize CSV summary variables with default values
    csv_avg_reward = csv_max_reward = csv_std_reward = csv_avg_alt = csv_max_alt = 0
    csv_summary = ""

    # Calculate AI metrics
    if trainer.episode_rewards:
        avg_reward = np.mean(trainer.episode_rewards)
        max_reward = np.max(trainer.episode_rewards)
        std_reward = np.std(trainer.episode_rewards)

        if trainer.max_altitudes:
            avg_altitude = np.mean(trainer.max_altitudes) / 1000
            max_altitude = np.max(trainer.max_altitudes) / 1000
        else:
            avg_altitude = max_altitude = 0

        # Calculate CSV metrics if available
        if csv_data is not None:
            if 'reward' in csv_data.columns:
                csv_avg_reward = csv_data['reward'].mean()
                csv_max_reward = csv_data['reward'].max()
                csv_std_reward = csv_data['reward'].std()
            else:
                csv_avg_reward = csv_max_reward = csv_std_reward = 0

            if 'altitude' in csv_data.columns:
                csv_avg_alt = csv_data['altitude'].mean() / 1000 if max(csv_data['altitude']) > 1000 else csv_data[
                    'altitude'].mean()
                csv_max_alt = csv_data['altitude'].max() / 1000 if max(csv_data['altitude']) > 1000 else csv_data[
                    'altitude'].max()
            else:
                csv_avg_alt = csv_max_alt = 0

            csv_summary = f"""
        CSV Data:
        • Avg Reward: {csv_avg_reward:.2f}
        • Max Reward: {csv_max_reward:.2f}
        • Std Reward: {csv_std_reward:.2f}
        • Avg Altitude: {csv_avg_alt:.1f} km
        • Max Altitude: {csv_max_alt:.1f} km
            """

        summary_text = f"""
        AI TRAINING SUMMARY (Episode {episode})

        AI Rewards:
        • Average: {avg_reward:.2f}
        • Maximum: {max_reward:.2f}
        • Std Dev: {std_reward:.2f}

        AI Altitude:
        • Average: {avg_altitude:.1f} km
        • Maximum: {max_altitude:.1f} km
        • Target: {trainer.env.target_altitude / 1000:.1f} km

        Test Results:
        • Successes: {successes}
        • Total Tests: {len(max_altitudes) if max_altitudes else 0}
        • Success Rate: {successes / len(max_altitudes) * 100 if max_altitudes else 0:.1f}%
        {csv_summary}
        """

        plt.text(0.1, 0.9, summary_text, transform=plt.gca().transAxes, fontsize=8,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.axis('off')
    plt.title('Performance Summary Comparison')

    # 12. Learning Progress (if we have enough data)
    plt.subplot(3, 4, 12)
    if len(trainer.episode_rewards) > 20:
        # Calculate improvement over time for AI
        quarter = len(trainer.episode_rewards) // 4
        if quarter > 0:
            first_quarter_avg = np.mean(trainer.episode_rewards[:quarter])
            last_quarter_avg = np.mean(trainer.episode_rewards[-quarter:])
            improvement = ((last_quarter_avg - first_quarter_avg) / abs(first_quarter_avg)) * 100

            labels = ['AI First 25%', 'AI Last 25%']
            values = [first_quarter_avg, last_quarter_avg]
            colors = ['lightblue', 'lightgreen']

            # Calculate improvement for CSV if available
            if csv_data is not None and 'reward' in csv_data.columns and len(csv_data) > 20:
                csv_quarter = len(csv_data) // 4
                csv_first_avg = csv_data['reward'][:csv_quarter].mean()
                csv_last_avg = csv_data['reward'][-csv_quarter:].mean()
                csv_improvement = ((csv_last_avg - csv_first_avg) / abs(csv_first_avg)) * 100

                labels.extend(['CSV First 25%', 'CSV Last 25%'])
                values.extend([csv_first_avg, csv_last_avg])
                colors.extend(['lightcoral', 'lightsalmon'])

            bars = plt.bar(labels, values, color=colors, alpha=0.8)
            plt.ylabel('Average Reward')
            plt.title(f'Learning Progress Comparison\nAI Improvement: {improvement:+.1f}%')

            # Add value labels on bars
            for bar, value in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                         f'{value:.1f}', ha='center', va='bottom', fontsize=8)

    plt.tight_layout()

    # Save with CSV indicator in filename
    filename_suffix = f"episode_{episode}_with_csv" if csv_file_path else f"episode_{episode}"
    plt.savefig(f'comprehensive_stats_{filename_suffix}.png', dpi=150, bbox_inches='tight')
    plt.close()

    if csv_file_path:
        print(f"✅ Comparison graphs saved with CSV data from {csv_file_path}")


def plot_detailed_trajectory(trainer, trajectory_data, title_suffix=""):
    """Plot detailed trajectory analysis"""
    if not trajectory_data:
        return

    fig = plt.figure(figsize=(18, 12))

    # Extract data
    times = [s['time'] for s in trajectory_data]
    altitudes = [s['altitude'] for s in trajectory_data]
    velocities = [s['velocity'] for s in trajectory_data]
    masses = [s['mass'] for s in trajectory_data]

    # 1. Altitude profile
    plt.subplot(2, 3, 1)
    plt.plot(times, [alt / 1000 for alt in altitudes], 'b-', linewidth=2)
    plt.axhline(y=trainer.env.target_altitude / 1000, color='r', linestyle='--',
                label=f'Target: {trainer.env.target_altitude / 1000:.0f}km')
    plt.xlabel('Time (s)')
    plt.ylabel('Altitude (km)')
    plt.title('Altitude vs Time')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 2. Velocity profile
    plt.subplot(2, 3, 2)
    plt.plot(times, velocities, 'g-', linewidth=2)
    plt.axhline(y=trainer.env.orbital_velocity, color='r', linestyle='--',
                label=f'Orbital: {trainer.env.orbital_velocity:.0f}m/s')
    plt.xlabel('Time (s)')
    plt.ylabel('Velocity (m/s)')
    plt.title('Velocity vs Time')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 3. Mass decay
    plt.subplot(2, 3, 3)
    plt.plot(times, [m / 1000 for m in masses], 'purple', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Mass (tons)')
    plt.title('Rocket Mass vs Time')
    plt.grid(True, alpha=0.3)

    # 4. Velocity vs Altitude (phase plot)
    plt.subplot(2, 3, 4)
    plt.plot([alt / 1000 for alt in altitudes], velocities, 'b-', linewidth=2)
    plt.axhline(y=trainer.env.orbital_velocity, color='r', linestyle='--')
    plt.axvline(x=trainer.env.target_altitude / 1000, color='r', linestyle='--')
    plt.xlabel('Altitude (km)')
    plt.ylabel('Velocity (m/s)')
    plt.title('Velocity vs Altitude (Phase Plot)')
    plt.grid(True, alpha=0.3)

    # 5. Energy analysis
    plt.subplot(2, 3, 5)
    kinetic_energy = [0.5 * v ** 2 / 1e6 for v in velocities]  # MJ/kg
    potential_energy = [9.8 * alt / 1000 for alt in altitudes]  # kJ/kg
    total_energy = [ke + pe / 1000 for ke, pe in zip(kinetic_energy, potential_energy)]  # MJ/kg

    plt.plot(times, kinetic_energy, 'r-', label='Kinetic Energy', alpha=0.8)
    plt.plot(times, [pe / 1000 for pe in potential_energy], 'g-', label='Potential Energy', alpha=0.8)
    plt.plot(times, total_energy, 'b-', label='Total Energy', linewidth=2)
    plt.xlabel('Time (s)')
    plt.ylabel('Energy (MJ/kg)')
    plt.title('Energy Analysis')
    plt.legend()
    plt.grid(True, alpha=0.3)

    # 6. Acceleration analysis (derived from velocity)
    plt.subplot(2, 3, 6)
    if len(velocities) > 1:
        acceleration = np.diff(velocities) / np.diff(times)
        # Pad to match time array length
        acceleration = np.concatenate(([acceleration[0]], acceleration))
        plt.plot(times, acceleration, 'orange', linewidth=2)
        plt.axhline(y=9.8, color='r', linestyle='--', label='Gravity (9.8 m/s²)')
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (m/s²)')
        plt.title('Acceleration Profile')
        plt.legend()
        plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'detailed_trajectory_{title_suffix}.png', dpi=150, bbox_inches='tight')
    plt.close()


def plot_real_time_training(trainer, current_episode):
    """Plot real-time training progress during training"""
    if current_episode % 50 != 0:  # Only plot every 50 episodes to save resources
        return

    fig = plt.figure(figsize=(15, 10))

    # 1. Reward progression
    plt.subplot(2, 3, 1)
    plt.plot(trainer.episode_rewards, 'b-', alpha=0.7)
    plt.title(f'Reward Progression (Episode {current_episode})')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.grid(True, alpha=0.3)

    # 2. Altitude progression
    plt.subplot(2, 3, 2)
    altitudes_km = [alt / 1000 for alt in trainer.max_altitudes]
    plt.plot(altitudes_km, 'g-', alpha=0.7)
    plt.axhline(y=trainer.env.target_altitude / 1000, color='r', linestyle='--')
    plt.title('Max Altitude Progression')
    plt.xlabel('Episode')
    plt.ylabel('Altitude (km)')
    plt.grid(True, alpha=0.3)

    # 3. Moving averages
    plt.subplot(2, 3, 3)
    if len(trainer.episode_rewards) > 20:
        window = 20
        reward_ma = np.convolve(trainer.episode_rewards, np.ones(window) / window, mode='valid')
        altitude_ma = np.convolve(altitudes_km, np.ones(window) / window, mode='valid')

        plt.plot(reward_ma, 'b-', label='Reward MA')
        plt.plot(altitude_ma, 'g-', label='Altitude MA')
        plt.title('Moving Averages (20 episodes)')
        plt.xlabel('Episode')
        plt.legend()
        plt.grid(True, alpha=0.3)

    # 4. Recent performance
    plt.subplot(2, 3, 4)
    if len(trainer.episode_rewards) > 100:
        recent_rewards = trainer.episode_rewards[-100:]
        recent_altitudes = altitudes_km[-100:]

        plt.plot(recent_rewards, 'b-', alpha=0.7, label='Rewards')
        plt.plot(recent_altitudes, 'g-', alpha=0.7, label='Altitude (km)')
        plt.title('Recent 100 Episodes')
        plt.xlabel('Episode (relative)')
        plt.legend()
        plt.grid(True, alpha=0.3)

    # 5. Success rate estimation
    plt.subplot(2, 3, 5)
    if trainer.max_altitudes:
        # Estimate success based on reaching target altitude
        success_estimates = []
        window_size = 50
        for i in range(window_size, len(trainer.max_altitudes)):
            window_altitudes = trainer.max_altitudes[i - window_size:i]
            successes_in_window = sum(1 for alt in window_altitudes if alt >= trainer.env.target_altitude * 0.8)
            success_estimates.append(successes_in_window / window_size * 100)

        if success_estimates:
            plt.plot(success_estimates, 'purple', linewidth=2)
            plt.title('Estimated Success Rate (%)')
            plt.xlabel(f'Episode (window: {window_size})')
            plt.ylabel('Success Rate %')
            plt.grid(True, alpha=0.3)

    # 6. Training statistics
    plt.subplot(2, 3, 6)
    stats_text = f"""
    Current Episode: {current_episode}

    Recent Performance:
    • Last Reward: {trainer.episode_rewards[-1]:.1f}
    • Last Altitude: {altitudes_km[-1]:.1f} km
    • Target: {trainer.env.target_altitude / 1000:.1f} km

    Statistics:
    • Avg Reward: {np.mean(trainer.episode_rewards):.1f}
    • Max Reward: {np.max(trainer.episode_rewards):.1f}
    • Max Altitude: {np.max(altitudes_km):.1f} km
    """
    plt.text(0.1, 0.9, stats_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    plt.axis('off')

    plt.tight_layout()
    plt.savefig(f'real_time_training_episode_{current_episode}.png', dpi=150, bbox_inches='tight')
    plt.close()


# Add these function calls to your training loop:

# In your train() method, add this after each episode:
# plot_real_time_training(self, episode)

# After training, call this with your test results:
# plot_comprehensive_stats(trainer, num_episodes, successes, max_altitudes, max_velocities, final_rewards)

# For specific trajectories:
# plot_detailed_trajectory(trainer, trainer.env.trajectory, "final_test")

class FixedRocketEnvironment(gym.Env):
    def __init__(self, rocket_params=None):
        super(FixedRocketEnvironment, self).__init__()

        # Realistic Falcon 9 first stage parameters
        self.rocket_params = {
            'dry_mass': 22800,  # Updated: First stage dry mass
            'fuel_mass': 410000,  # Updated: First stage fuel
            'thrust': 7600e3,
            'isp': 282,
            # Second stage parameters
            'second_stage_dry_mass': 9500,
            'second_stage_fuel': 110000,
            'second_stage_thrust': 934e3,
            'second_stage_isp': 348,
            'drag_coeff': 0.5,
            'cross_section': 10.9,
            'burn_time': 162,
        }

        if rocket_params:
            self.rocket_params.update(rocket_params)

        # Physical constants
        self.g0 = 9.80665  # m/s²
        self.R_earth = 6371e3  # m

        # Target
        self.target_altitude = 400e3  # Higher target for two-stage
        self.orbital_velocity = 7800

        # Environment parameters
        self.max_steps = 2000
        self.dt = 0.1

        # Action space: [throttle]
        self.action_space = spaces.Box(
            low=np.array([0.0], dtype=np.float32),
            high=np.array([1.0], dtype=np.float32),
            dtype=np.float32
        )

        # Stage management - ADD THIS
        self.first_stage_active = True
        self.second_stage_active = False
        self.stage_separated = False
        self.stage_separation_altitude = 80e3  # Separate at 80km

        # Calculate total initial mass (both stages)
        self.initial_total_mass = (self.rocket_params['dry_mass'] +
                                   self.rocket_params['fuel_mass'] +
                                   self.rocket_params['second_stage_dry_mass'] +
                                   self.rocket_params['second_stage_fuel'])

        # Update observation space to include stage info
        self.observation_space = spaces.Box(
            low=np.array([0, -1000, 0, -1], dtype=np.float32),  # Added 4th dimension
            high=np.array([1000e3, 10000, 1, 1], dtype=np.float32),
            dtype=np.float32
        )

        print("🚀 Two-stage rocket environment initialized")
        print(
            f"   Stage 1: {self.rocket_params['dry_mass'] / 1000:.0f}t dry, {self.rocket_params['fuel_mass'] / 1000:.0f}t fuel")
        print(
            f"   Stage 2: {self.rocket_params['second_stage_dry_mass'] / 1000:.0f}t dry, {self.rocket_params['second_stage_fuel'] / 1000:.0f}t fuel")

        self.reset()

    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)

        # Initial state
        self.altitude = 0.0
        self.velocity = 0.0
        self.mass = self.initial_total_mass  # Start with full mass
        self.time = 0.0
        self.step_count = 0
        self.fuel_used = 0.0
        self.has_lifted_off = False

        # Reset stage management
        self.first_stage_active = True
        self.second_stage_active = False
        self.stage_separated = False

        self.trajectory = []
        self.record_state()

        obs = self.get_observation()
        return obs, {}

    def get_observation(self):
        # Enhanced observation with stage info
        if self.first_stage_active:
            # First stage fuel calculation
            current_fuel = self.mass - (self.rocket_params['dry_mass'] +
                                        self.rocket_params['second_stage_dry_mass'] +
                                        self.rocket_params['second_stage_fuel'])
            total_fuel = self.rocket_params['fuel_mass']
            stage_indicator = 1.0  # First stage
        elif self.second_stage_active:
            # Second stage fuel calculation
            current_fuel = self.mass - self.rocket_params['second_stage_dry_mass']
            total_fuel = self.rocket_params['second_stage_fuel']
            stage_indicator = 0.0  # Second stage
        else:
            # Coasting phase
            current_fuel = 0
            total_fuel = 1
            stage_indicator = -1.0

        mass_ratio = current_fuel / total_fuel if total_fuel > 0 else 0

        obs = np.array([
            self.altitude / 1000e3,
            self.velocity / 10000,
            mass_ratio,
            stage_indicator
        ], dtype=np.float32)

        return obs

    def record_state(self):
        """Record the current state to trajectory history"""
        self.trajectory.append({
            'time': self.time,
            'altitude': self.altitude,
            'velocity': self.velocity,
            'mass': self.mass,
            # Optional: Add stage info for debugging
            'stage': '1st' if self.first_stage_active else '2nd' if self.second_stage_active else 'coast'
        })

    def step(self, action):
        self.step_count += 1
        self.time += self.dt

        # Handle stage separation - ADD THIS
        if (self.first_stage_active and
                self.altitude >= self.stage_separation_altitude and
                not self.stage_separated):
            self.separate_stages()

        throttle = np.clip(action[0], 0.0, 1.0)

        # Determine which stage is active and calculate thrust accordingly
        if self.first_stage_active:
            thrust, mdot = self.calculate_first_stage_thrust(throttle)
        elif self.second_stage_active:
            thrust, mdot = self.calculate_second_stage_thrust(throttle)
        else:
            thrust, mdot = 0, 0  # Coasting phase

        # Check if we have fuel (existing logic)
        current_fuel = self.mass - self.rocket_params['dry_mass']
        if current_fuel <= 0:
            thrust = 0
            mdot = 0

        # Rest of your existing physics calculations remain the SAME
        gravity_force = self.mass * 9.8

        if self.altitude > 0 and abs(self.velocity) > 0:
            density = 1.225 * np.exp(-self.altitude / 8500)
            drag_force = 0.5 * density * self.velocity ** 2 * \
                         self.rocket_params['drag_coeff'] * self.rocket_params['cross_section']
            if self.velocity > 0:
                drag_force = -drag_force
            else:
                drag_force = abs(drag_force)
        else:
            drag_force = 0

        net_force = thrust - gravity_force + drag_force
        acceleration = net_force / self.mass

        new_velocity = self.velocity + acceleration * self.dt
        new_altitude = self.altitude + self.velocity * self.dt + 0.5 * acceleration * self.dt ** 2
        new_mass = self.mass - mdot * self.dt

        # Enhanced mass limits for staging
        if self.first_stage_active:
            min_mass = (self.rocket_params['dry_mass'] +
                        self.rocket_params['second_stage_dry_mass'] +
                        self.rocket_params['second_stage_fuel'])
        elif self.second_stage_active:
            min_mass = self.rocket_params['second_stage_dry_mass']
        else:
            min_mass = self.rocket_params['second_stage_dry_mass']

        if new_mass < min_mass:
            new_mass = min_mass
            # Handle stage burnout
            if self.first_stage_active and new_mass <= min_mass:
                if not self.stage_separated:
                    self.separate_stages()
            elif self.second_stage_active and new_mass <= self.rocket_params['second_stage_dry_mass']:
                self.second_stage_active = False

        # Update state
        self.velocity = new_velocity
        self.altitude = max(new_altitude, 0.0)
        self.mass = new_mass
        self.fuel_used += mdot * self.dt

        # Check if we've lifted off
        if self.altitude > 0.1 and not self.has_lifted_off:
            self.has_lifted_off = True
            print(f"LIFT-OFF! at step {self.step_count}")

        self.record_state()

        # Calculate reward
        reward, done = self.calculate_reward()

        # Check termination conditions
        if self.altitude <= 0 and self.velocity < -1.0:
            reward = -10
            done = True
            if self.step_count == 1:
                print(f"Immediate crash - throttle was {throttle:.2f}")

        if self.step_count >= self.max_steps:
            done = True

        current_fuel = self.mass - self.rocket_params['dry_mass']
        if current_fuel <= 0 and not done:
            reward = self.final_reward()
            done = True

        truncated = False

        # Enhanced debug info with stage info
        if self.step_count <= 3 or (
                self.step_count <= 10 and self.step_count % 2 == 0) or self.step_count % 100 == 0 or done:
            stage = "1st" if self.first_stage_active else "2nd" if self.second_stage_active else "COAST"
            status = "CRASHED" if done and self.altitude <= 0 else "FLYING"
            print(
                f"Step {self.step_count} [{stage}]: throttle={throttle:.2f}, alt={self.altitude:.1f}m, vel={self.velocity:.1f}m/s, mass={self.mass:.0f}kg, reward={reward:.2f} [{status}]")

        obs = self.get_observation()
        return obs, reward, done, truncated, {}

    # ADD THESE NEW METHODS FOR STAGE MANAGEMENT:
    def calculate_first_stage_thrust(self, throttle):
        """Calculate thrust and mass flow for first stage"""
        current_fuel = self.mass - (self.rocket_params['dry_mass'] +
                                    self.rocket_params['second_stage_dry_mass'] +
                                    self.rocket_params['second_stage_fuel'])
        if current_fuel <= 0:
            return 0, 0

        thrust = self.rocket_params['thrust'] * throttle
        mdot = thrust / (self.rocket_params['isp'] * self.g0)

        fuel_used = mdot * self.dt
        if fuel_used > current_fuel:
            fuel_used = current_fuel
            mdot = fuel_used / self.dt
            thrust = mdot * self.rocket_params['isp'] * self.g0

        return thrust, mdot

    def calculate_second_stage_thrust(self, throttle):
        """Calculate thrust and mass flow for second stage"""
        current_fuel = self.mass - self.rocket_params['second_stage_dry_mass']
        if current_fuel <= 0:
            return 0, 0

        thrust = self.rocket_params['second_stage_thrust'] * throttle
        mdot = thrust / (self.rocket_params['second_stage_isp'] * self.g0)

        fuel_used = mdot * self.dt
        if fuel_used > current_fuel:
            fuel_used = current_fuel
            mdot = fuel_used / self.dt
            thrust = mdot * self.rocket_params['second_stage_isp'] * self.g0

        return thrust, mdot

    def separate_stages(self):
        """Separate first stage and activate second stage"""
        if self.first_stage_active and not self.stage_separated:
            # Jettison first stage - mass becomes just second stage
            self.mass = (self.rocket_params['second_stage_dry_mass'] +
                         self.rocket_params['second_stage_fuel'])
            self.first_stage_active = False
            self.second_stage_active = True
            self.stage_separated = True
            print(f"🚀 STAGE SEPARATION at {self.altitude / 1000:.1f}km! Second stage ignition!")

    # Enhanced reward function for staging
    def calculate_reward(self):
        reward = 0

        # Heavy penalty for crashing
        if self.altitude <= 0 and self.velocity < -1.0:
            return -50, True

        # Base survival reward
        reward += 0.01

        # Altitude reward (scaled for orbital target)
        altitude_reward = (self.altitude / self.target_altitude) * 20
        reward += altitude_reward

        # Velocity reward - CRITICAL for orbit
        if self.velocity > 0:
            velocity_bonus = (self.velocity / self.orbital_velocity) * 50
            reward += velocity_bonus

        # Stage separation bonus - ADD THIS
        if self.stage_separated and not hasattr(self, 'separation_bonus_given'):
            reward += 500  # Big bonus for successful staging
            self.separation_bonus_given = True

        # Orbital energy reward (combines altitude and velocity)
        if self.altitude > 100e3:
            orbital_energy = (0.5 * self.velocity ** 2 - 3.986e14 / (self.altitude + 6371e3))
            reward += orbital_energy * 1e-7

        # Success bonuses
        if self.altitude >= 100e3:
            reward += 100
        if self.altitude >= self.target_altitude and self.velocity >= self.orbital_velocity * 0.9:
            reward += 10000
            print(f"ORBIT ACHIEVED! Altitude: {self.altitude / 1000:.1f}km, Velocity: {self.velocity:.1f}m/s")
            return reward, True

        return reward, False

    def final_reward(self):
        """Final reward when out of fuel"""
        if self.altitude >= self.target_altitude:
            return 1000
        else:
            altitude_ratio = self.altitude / self.target_altitude
            return altitude_ratio * 200


class SimpleActorNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super(SimpleActorNetwork, self).__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim * 2)

        # Simple initialization
        nn.init.normal_(self.fc1.weight, mean=0.0, std=0.1)
        nn.init.normal_(self.fc2.weight, mean=0.0, std=0.1)
        nn.init.normal_(self.fc3.weight, mean=0.0, std=0.1)

    def forward(self, x):
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)

        mean, log_std = x.chunk(2, dim=-1)
        log_std = torch.clamp(log_std, -20, 2)

        return mean, log_std


class SimpleCriticNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim=64):
        super(SimpleCriticNetwork, self).__init__()

        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, 1)

        # Simple initialization
        nn.init.normal_(self.fc1.weight, mean=0.0, std=0.1)
        nn.init.normal_(self.fc2.weight, mean=0.0, std=0.1)
        nn.init.normal_(self.fc3.weight, mean=0.0, std=0.1)

    def forward(self, x):
        x = torch.tanh(self.fc1(x))
        x = torch.tanh(self.fc2(x))
        x = self.fc3(x)
        return x


class BetterActorNetwork(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(BetterActorNetwork, self).__init__()

        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),  # Layer normalization for stability
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.Tanh(),
        )

        self.mean_head = nn.Linear(hidden_dim // 2, action_dim)
        self.log_std_head = nn.Linear(hidden_dim // 2, action_dim)

        # Better initialization
        nn.init.orthogonal_(self.mean_head.weight, gain=0.01)
        nn.init.constant_(self.mean_head.bias, 0.0)
        nn.init.constant_(self.log_std_head.bias, -1.0)  # Start with higher exploration

    def forward(self, x):
        features = self.net(x)
        mean = self.mean_head(features)
        log_std = self.log_std_head(features)
        log_std = torch.clamp(log_std, -20, 2)
        return mean, log_std


class BetterCriticNetwork(nn.Module):
    def __init__(self, state_dim, hidden_dim=128):
        super(BetterCriticNetwork, self).__init__()

        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.LayerNorm(hidden_dim // 2),
            nn.Tanh(),
            nn.Linear(hidden_dim // 2, 1)
        )

        # Better initialization
        for layer in self.net:
            if isinstance(layer, nn.Linear):
                nn.init.orthogonal_(layer.weight, gain=1.0)
                nn.init.constant_(layer.bias, 0.0)

    def forward(self, x):
        return self.net(x)


class SimplePPOAgent:
    def __init__(self, state_dim, action_dim, lr=3e-4, gamma=0.99, gae_lambda=0.95,
                 clip_epsilon=0.2, ppo_epochs=10, batch_size=128, use_better_networks=True):  # Add option
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Use better networks if specified
        if use_better_networks:
            self.actor = BetterActorNetwork(state_dim, action_dim)
            self.critic = BetterCriticNetwork(state_dim)
            print("✅ Using BetterActorNetwork and BetterCriticNetwork")
        else:
            self.actor = SimpleActorNetwork(state_dim, action_dim)
            self.critic = SimpleCriticNetwork(state_dim)
            print("✅ Using SimpleActorNetwork and SimpleCriticNetwork")

        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=lr, weight_decay=1e-5)
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=lr, weight_decay=1e-5)

        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.ppo_epochs = ppo_epochs
        self.batch_size = batch_size

        # Exploration tracking
        self.episode_count = 0
        self.min_std = 0.1
        self.initial_std = 1.0

        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []
        self.log_probs = []

    def get_action(self, state, deterministic=False):
        try:
            if not isinstance(state, np.ndarray):
                state = np.array(state, dtype=np.float32)

            state_tensor = torch.FloatTensor(state).unsqueeze(0)

            with torch.no_grad():
                mean, log_std = self.actor(state_tensor)

                # Add exploration decay
                if not deterministic and self.episode_count > 0:
                    decay_factor = max(0.5, 1.0 - (self.episode_count / 5000))  # Slow decay over 5000 episodes
                    log_std = log_std * decay_factor
                    log_std = torch.clamp(log_std, math.log(self.min_std), math.log(self.initial_std))

                if torch.isnan(mean).any() or torch.isnan(log_std).any():
                    action = np.array([0.9], dtype=np.float32)
                    log_prob = 0.0
                    return action, log_prob

                std = log_std.exp()

            if deterministic:
                action = torch.tanh(mean)
            else:
                normal = Normal(mean, std)
                action = torch.tanh(normal.sample())

            action = action.squeeze(0).numpy().astype(np.float32)

            # Calculate log probability
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            mean, log_std = self.actor(state_tensor)
            std = log_std.exp()
            normal = Normal(mean, std)

            action_tensor = torch.FloatTensor(action).unsqueeze(0)
            action_pre_tanh = 0.5 * torch.log((1 + action_tensor) / (1 - action_tensor))
            action_pre_tanh = torch.clamp(action_pre_tanh, -10, 10)
            log_prob = normal.log_prob(action_pre_tanh).sum(dim=-1).item()

            return action, log_prob

        except Exception as e:
            print(f"Error in get_action: {e}")
            action = np.array([0.9], dtype=np.float32)
            log_prob = 0.0
            return action, log_prob

    def store_transition(self, state, action, reward, next_state, done, log_prob):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)
        self.log_probs.append(log_prob)

    def update(self):
        if len(self.states) < self.batch_size:
            return

        try:
            # Convert to tensors
            states = torch.FloatTensor(np.array(self.states))
            actions = torch.FloatTensor(np.array(self.actions))
            old_log_probs = torch.FloatTensor(np.array(self.log_probs))
            rewards = torch.FloatTensor(np.array(self.rewards))
            next_states = torch.FloatTensor(np.array(self.next_states))
            dones = torch.FloatTensor(np.array(self.dones))

            # Compute values
            with torch.no_grad():
                values = self.critic(states).squeeze()
                next_values = self.critic(next_states).squeeze()

            # IMPROVED: More robust GAE advantage calculation
            advantages = []
            returns = []
            gae = 0

            # Calculate advantages in reverse
            for t in reversed(range(len(rewards))):
                if t == len(rewards) - 1:
                    next_non_terminal = 1.0 - dones[t]
                    next_value = next_values[t]
                else:
                    next_non_terminal = 1.0 - dones[t]
                    next_value = values[t + 1]

                delta = rewards[t] + self.gamma * next_value * next_non_terminal - values[t]
                gae = delta + self.gamma * self.gae_lambda * next_non_terminal * gae
                advantages.insert(0, gae)
                returns.insert(0, gae + values[t])

            advantages = torch.FloatTensor(advantages)
            returns = torch.FloatTensor(returns)

            # Normalize advantages - CRITICAL FOR STABILITY
            if len(advantages) > 1:
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            # Track losses for debugging
            total_actor_loss = 0
            total_critic_loss = 0
            update_count = 0

            # PPO update with multiple epochs
            for epoch in range(self.ppo_epochs):
                # Shuffle indices for each epoch
                indices = torch.randperm(len(states))

                for start in range(0, len(states), self.batch_size):
                    end = start + self.batch_size
                    batch_indices = indices[start:end]

                    batch_states = states[batch_indices]
                    batch_actions = actions[batch_indices]
                    batch_old_log_probs = old_log_probs[batch_indices]
                    batch_advantages = advantages[batch_indices]
                    batch_returns = returns[batch_indices]

                    # === ACTOR UPDATE ===
                    mean, log_std = self.actor(batch_states)

                    # Skip if numerical issues
                    if torch.isnan(mean).any() or torch.isnan(log_std).any():
                        print("Warning: NaN in actor output, skipping batch")
                        continue

                    std = log_std.exp()
                    normal = Normal(mean, std)

                    # Calculate log probability with numerical stability
                    action_pre_tanh = 0.5 * torch.log((1 + batch_actions) / (1 - batch_actions))
                    action_pre_tanh = torch.clamp(action_pre_tanh, -10, 10)
                    new_log_probs = normal.log_prob(action_pre_tanh).sum(dim=-1)

                    # PPO objective
                    ratio = torch.exp(new_log_probs - batch_old_log_probs)

                    # Clipped surrogate objective
                    surr1 = ratio * batch_advantages
                    surr2 = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon) * batch_advantages
                    actor_loss = -torch.min(surr1, surr2).mean()

                    # === CRITIC UPDATE ===
                    current_values = self.critic(batch_states).squeeze()
                    critic_loss = nn.MSELoss()(current_values, batch_returns)

                    # === GRADIENT UPDATES ===
                    # Actor update
                    self.actor_optimizer.zero_grad()
                    actor_loss.backward()
                    # More aggressive gradient clipping for actor
                    torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
                    self.actor_optimizer.step()

                    # Critic update
                    self.critic_optimizer.zero_grad()
                    critic_loss.backward()
                    # Less aggressive gradient clipping for critic
                    torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 1.0)
                    self.critic_optimizer.step()

                    total_actor_loss += actor_loss.item()
                    total_critic_loss += critic_loss.item()
                    update_count += 1

            # Print detailed update information
            if update_count > 0:
                avg_actor_loss = total_actor_loss / update_count
                avg_critic_loss = total_critic_loss / update_count
                advantage_mean = advantages.mean().item()
                advantage_std = advantages.std().item()

                print(f"Update: samples={len(self.states)}, "
                      f"actor_loss={avg_actor_loss:.4f}, "
                      f"critic_loss={avg_critic_loss:.4f}, "
                      f"advantage_mean={advantage_mean:.4f}±{advantage_std:.4f}")

            # Increment episode count for exploration scheduling
            self.episode_count += 1

        except Exception as e:
            print(f"Error in update: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Clear memory
            self.states.clear()
            self.actions.clear()
            self.rewards.clear()
            self.next_states.clear()
            self.dones.clear()
            self.log_probs.clear()


class OrbitalPPOAgent(SimplePPOAgent):
    def __init__(self, state_dim, action_dim, lr=1e-4, gamma=0.995, gae_lambda=0.95,
                 clip_epsilon=0.1, ppo_epochs=10, batch_size=128):
        super().__init__(state_dim, action_dim, lr, gamma, gae_lambda, clip_epsilon, ppo_epochs, batch_size)

        # Larger networks for complex orbital mechanics
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.Tanh(),
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 64),
            nn.Tanh(),
            nn.Linear(64, action_dim * 2)
        )

        self.critic = nn.Sequential(
            nn.Linear(state_dim, 256),
            nn.Tanh(),
            nn.Linear(256, 128),
            nn.Tanh(),
            nn.Linear(128, 64),
            nn.Tanh(),
            nn.Linear(64, 1)
        )


class OrbitalRocketEnvironment(FixedRocketEnvironment):
    """Enhanced environment for orbital training"""

    def __init__(self, rocket_params=None):
        super().__init__(rocket_params)
        # Higher target for orbital training
        self.target_altitude = 200e3  # Start with 200km
        self.orbital_velocity = 7800  # m/s for LEO


class OrbitalRocketTrainer:
    def __init__(self, rocket_params=None):
        # Use OrbitalRocketEnvironment for orbital training
        self.env = OrbitalRocketEnvironment(rocket_params)
        self.agent = SimplePPOAgent(
            state_dim=self.env.observation_space.shape[0],
            action_dim=self.env.action_space.shape[0]
        )

        self.episode_rewards = []
        self.max_altitudes = []
        self.max_velocities = []  # ADD THIS LINE

    def train(self, num_episodes=1000, save_interval=100):
        print("Starting ORBITAL rocket training...")

        success_count = 0
        best_max_altitude = 0

        for episode in range(num_episodes):
            state, _ = self.env.reset()
            episode_reward = 0
            done = False
            step_count = 0

            while not done and step_count < 3000:
                action, log_prob = self.agent.get_action(state)
                next_state, reward, done, truncated, _ = self.env.step(action)

                self.agent.store_transition(state, action, reward, next_state, done, log_prob)

                state = next_state
                episode_reward += reward
                step_count += 1

            # Update more frequently - every episode with enough samples
            if len(self.agent.states) >= self.agent.batch_size:
                self.agent.update()

            # Progressive difficulty
            max_alt = max([s['altitude'] for s in self.env.trajectory]) if self.env.trajectory else 0
            max_vel = max([s['velocity'] for s in self.env.trajectory]) if self.env.trajectory else 0

            # Record progress
            self.episode_rewards.append(episode_reward)
            self.max_altitudes.append(max_alt)
            self.max_velocities.append(max_vel)

            # Track best performance
            if max_alt > best_max_altitude:
                best_max_altitude = max_alt
                print(f"🏆 NEW RECORD! Altitude: {max_alt / 1000:.1f}km")

            # Real-time plotting
            if episode % 50 == 0:
                plot_real_time_training(self, episode)

            # Print progress
            if episode % 50 == 0:
                print(
                    f"Episode {episode}: Max Alt={max_alt / 1000:.1f}km, Max Vel={max_vel:.0f}m/s, Reward={episode_reward:.1f}")

            # Smarter difficulty progression
            performance_ratio = max_alt / self.env.target_altitude
            if performance_ratio > 0.8 and max_vel > self.env.orbital_velocity * 0.8:
                success_count += 1
                if success_count >= 2:  # Need consistent high performance
                    current_target = self.env.target_altitude
                    new_target = min(current_target * 1.1, 600e3)  # Smaller increments
                    if new_target > current_target:
                        self.env.target_altitude = new_target
                        print(f"🎯 Target increased to {new_target / 1000:.0f} km")
                        success_count = 0

            # Plot progress
            if episode % 100 == 0 and episode > 0:
                recent_improvement = np.mean(self.episode_rewards[-100:]) - np.mean(self.episode_rewards[-200:-100])
                if recent_improvement < 1.0:  # Stagnant performance
                    # Reduce learning rate
                    for param_group in self.agent.actor_optimizer.param_groups:
                        param_group['lr'] *= 0.8
                    for param_group in self.agent.critic_optimizer.param_groups:
                        param_group['lr'] *= 0.8
                    print(f"Reduced learning rate to {self.agent.actor_optimizer.param_groups[0]['lr']:.2e}")

            # Auto-save every N episodes
            if episode % save_interval == 0 and episode > 0:
                self.save_checkpoint(episode)

        # Final training plot
        plot_real_time_training(self, num_episodes)

    def plot_progress(self, episode):
        plt.figure(figsize=(12, 4))

        plt.subplot(1, 2, 1)
        plt.plot(self.episode_rewards)
        plt.title('Episode Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')

        plt.subplot(1, 2, 2)
        altitudes_km = [alt / 1000 for alt in self.max_altitudes]
        plt.plot(altitudes_km)
        plt.axhline(y=self.env.target_altitude / 1000, color='r', linestyle='--', label='Target')
        plt.title('Max Altitude Reached')
        plt.xlabel('Episode')
        plt.ylabel('Altitude (km)')
        plt.legend()

        plt.tight_layout()
        plt.savefig(f'orbital_progress_{episode}.png')
        plt.close()

    def plot_trajectory(self, filename_suffix=""):
        if not self.env.trajectory:
            return

        times = [s['time'] for s in self.env.trajectory]
        altitudes = [s['altitude'] for s in self.env.trajectory]
        velocities = [s['velocity'] for s in self.env.trajectory]
        masses = [s['mass'] for s in self.env.trajectory]

        plt.figure(figsize=(15, 5))

        plt.subplot(1, 3, 1)
        plt.plot(times, [alt / 1000 for alt in altitudes])
        plt.axhline(y=self.env.target_altitude / 1000, color='r', linestyle='--', label='Target Orbit')
        plt.title('Altitude')
        plt.xlabel('Time (s)')
        plt.ylabel('Altitude (km)')
        plt.legend()

        plt.subplot(1, 3, 2)
        plt.plot(times, velocities)
        plt.axhline(y=self.env.orbital_velocity, color='r', linestyle='--', label='Orbital Velocity')
        plt.title('Velocity')
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s)')
        plt.legend()

        plt.subplot(1, 3, 3)
        plt.plot(times, masses)
        plt.title('Rocket Mass')
        plt.xlabel('Time (s)')
        plt.ylabel('Mass (kg)')

        plt.tight_layout()
        plt.savefig(f'orbital_trajectory_{filename_suffix}.png')
        plt.close()


class FixedRocketTrainer:
    def __init__(self, rocket_params=None):
        # Use FixedRocketEnvironment instead of OrbitalRocketTrainer
        self.env = FixedRocketEnvironment(rocket_params)
        self.agent = SimplePPOAgent(
            state_dim=self.env.observation_space.shape[0],
            action_dim=self.env.action_space.shape[0]
        )

        self.episode_rewards = []
        self.max_altitudes = []

    def train(self, num_episodes=1000):
        print("Starting FIXED rocket training...")

        for episode in range(num_episodes):
            state, _ = self.env.reset()
            episode_reward = 0
            done = False

            step_count = 0
            while not done and step_count < 3000:
                action, log_prob = self.agent.get_action(state)
                next_state, reward, done, truncated, _ = self.env.step(action)

                self.agent.store_transition(state, action, reward, next_state, done, log_prob)

                state = next_state
                episode_reward += reward
                step_count += 1

            # Update more frequently with larger batches
            if len(self.agent.states) >= 64:
                self.agent.update()

            # Record progress
            max_alt = max([s['altitude'] for s in self.env.trajectory]) if self.env.trajectory else 0
            max_vel = max([s['velocity'] for s in self.env.trajectory]) if self.env.trajectory else 0

            self.episode_rewards.append(episode_reward)
            self.max_altitudes.append(max_alt)

            # Print progress every 50 episodes
            if episode % 50 == 0:
                print(
                    f"Episode {episode}: Max Alt={max_alt / 1000:.1f}km, Max Vel={max_vel:.0f}m/s, Reward={episode_reward:.1f}")

            # Plot progress every 100 episodes
            if episode % 100 == 0:
                self.plot_progress(episode)

    def plot_progress(self, episode):
        plt.figure(figsize=(12, 4))

        plt.subplot(1, 2, 1)
        plt.plot(self.episode_rewards)
        plt.title('Episode Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')

        plt.subplot(1, 2, 2)
        altitudes_km = [alt / 1000 for alt in self.max_altitudes]
        plt.plot(altitudes_km)
        plt.axhline(y=self.env.target_altitude / 1000, color='r', linestyle='--', label='Target')
        plt.title('Max Altitude Reached')
        plt.xlabel('Episode')
        plt.ylabel('Altitude (km)')
        plt.legend()

        plt.tight_layout()
        plt.savefig(f'fixed_progress_{episode}.png')
        plt.close()

    def plot_trajectory(self, episode):
        if not self.env.trajectory:
            return

        times = [s['time'] for s in self.env.trajectory]
        altitudes = [s['altitude'] for s in self.env.trajectory]
        velocities = [s['velocity'] for s in self.env.trajectory]
        masses = [s['mass'] for s in self.env.trajectory]

        plt.figure(figsize=(15, 5))

        plt.subplot(1, 3, 1)
        plt.plot(times, [alt / 1000 for alt in altitudes])
        plt.axhline(y=self.env.target_altitude / 1000, color='r', linestyle='--', label='Target')
        plt.title('Altitude')
        plt.xlabel('Time (s)')
        plt.ylabel('Altitude (km)')
        plt.legend()

        plt.subplot(1, 3, 2)
        plt.plot(times, velocities)
        plt.title('Velocity')
        plt.xlabel('Time (s)')
        plt.ylabel('Velocity (m/s)')

        plt.subplot(1, 3, 3)
        plt.plot(times, masses)
        plt.title('Rocket Mass')
        plt.xlabel('Time (s)')
        plt.ylabel('Mass (kg)')

        plt.tight_layout()
        plt.savefig(f'fixed_trajectory_{episode}.png')
        plt.close()


def save_model(agent, filename="trained_orbital_agent.pth"):
    torch.save({
        'actor_state_dict': agent.actor.state_dict(),
        'critic_state_dict': agent.critic.state_dict(),
        'actor_optimizer_state_dict': agent.actor_optimizer.state_dict(),
        'critic_optimizer_state_dict': agent.critic_optimizer.state_dict(),
    }, filename)
    print(f"Model saved to {filename}")


def final_test(trainer, num_tests=10):
    print(f"\n=== FINAL PERFORMANCE TEST ({num_tests} runs) ===")

    successes = 0
    max_altitudes = []
    max_velocities = []
    final_rewards = []
    best_trajectory = None  # ADD THIS LINE
    best_reward = -float('inf')  # ADD THIS LINE

    for test in range(num_tests):
        state, _ = trainer.env.reset()
        episode_reward = 0
        done = False
        step_count = 0

        # Use deterministic actions for testing
        while not done and step_count < 4000:
            action, _ = trainer.agent.get_action(state, deterministic=True)
            next_state, reward, done, truncated, _ = trainer.env.step(action)

            state = next_state
            episode_reward += reward
            step_count += 1

        # Analyze results
        max_alt = max([s['altitude'] for s in trainer.env.trajectory]) if trainer.env.trajectory else 0
        max_vel = max([s['velocity'] for s in trainer.env.trajectory]) if trainer.env.trajectory else 0
        final_alt = trainer.env.trajectory[-1]['altitude'] if trainer.env.trajectory else 0
        final_vel = trainer.env.trajectory[-1]['velocity'] if trainer.env.trajectory else 0

        max_altitudes.append(max_alt)
        max_velocities.append(max_vel)
        final_rewards.append(episode_reward)

        # ========== SAVE BEST TRAJECTORY ==========
        if episode_reward > best_reward:
            best_reward = episode_reward
            best_trajectory = trainer.env.trajectory.copy()  # Save a copy
        # ========== END SAVE BEST TRAJECTORY ==========

        # Check if orbit was achieved
        orbit_achieved = (final_alt >= trainer.env.target_altitude * 0.95 and
                          final_vel >= trainer.env.orbital_velocity * 0.9)

        if orbit_achieved:
            successes += 1
            status = "SUCCESS - ORBIT ACHIEVED! 🚀"
        elif final_alt >= trainer.env.target_altitude * 0.8:
            status = "PARTIAL - High altitude but low velocity"
        elif final_alt >= 100e3:
            status = "SUBORBITAL - Reached space"
        else:
            status = "FAILED - Did not reach target"

        print(f"Test {test + 1}: Max Alt={max_alt / 1000:.1f}km, Max Vel={max_vel:.0f}m/s, "
              f"Final Alt={final_alt / 1000:.1f}km, Final Vel={final_vel:.0f}m/s - {status}")

    # Print summary statistics
    print(f"\n=== TEST SUMMARY ===")
    print(f"Success Rate: {successes}/{num_tests} ({successes / num_tests * 100:.1f}%)")
    print(f"Average Max Altitude: {np.mean(max_altitudes) / 1000:.1f} ± {np.std(max_altitudes) / 1000:.1f} km")
    print(f"Average Max Velocity: {np.mean(max_velocities):.0f} ± {np.std(max_velocities):.0f} m/s")
    print(f"Average Reward: {np.mean(final_rewards):.2f} ± {np.std(final_rewards):.2f}")

    # ========== RETURN ALL DATA ==========
    return successes, max_altitudes, max_velocities, final_rewards, best_trajectory
    # ========== END RETURN ALL DATA ==========


# Main execution
if __name__ == "__main__":
    # Enhanced rocket parameters for orbital flight
    rocket_params = {
        'dry_mass': 22800,  # First stage dry mass
        'fuel_mass': 410000,  # First stage fuel
        'thrust': 7600e3,
        'isp': 282,
        'second_stage_dry_mass': 9500,
        'second_stage_fuel': 110000,
        'second_stage_thrust': 934e3,
        'second_stage_isp': 348,
    }

    # Choose which trainer to use
    use_orbital = True  # Set to False to use FixedRocketTrainer

    if use_orbital:
        print("=== ORBITAL ROCKET TRAINING ===")
        trainer = OrbitalRocketTrainer(rocket_params)
    else:
        print("=== FIXED ROCKET TRAINING ===")
        trainer = FixedRocketTrainer(rocket_params)

    # Train the agent
    print("🚀 Starting training...")
    trainer.train(num_episodes=10000)
    print("✅ Training completed!")

    # Run final test and get all data
    print("📊 Running final performance tests...")
    successes, max_altitudes, max_velocities, final_rewards, best_trajectory = final_test(trainer, 5)

    # ========== GENERATE ALL GRAPHS HERE ==========
    print("📈 Generating comprehensive graphs...")

    # Ask user for CSV file path
    csv_path = input("Enter path to CSV file for comparison (or press Enter to skip): ").strip()
    csv_path = csv_path if csv_path else None

    if csv_path:
        print(f"📊 Loading comparison data from: {csv_path}")

    # 1. Comprehensive stats with optional CSV comparison
    plot_comprehensive_stats_with_csv(
        trainer,
        len(trainer.episode_rewards),
        successes,
        max_altitudes,
        max_velocities,
        final_rewards,
        csv_file_path=csv_path
    )

    # 2. Detailed trajectory of best run
    if best_trajectory:
        plot_detailed_trajectory(trainer, best_trajectory, "best_performance")
        print("✅ Best trajectory graph saved!")

    # 3. Final trajectory (last test run)
    if trainer.env.trajectory:
        plot_detailed_trajectory(trainer, trainer.env.trajectory, "final_test")
        print("✅ Final trajectory graph saved!")

    print("🎉 All graphs generated successfully!")
    # ========== END GRAPH GENERATION ==========

    # Save the trained model
    save_model(trainer.agent)

    print("\n=== TRAINING COMPLETE ===")
    if successes > 0:
        print(f"🎉 Successfully achieved orbit in {successes} out of 5 tests!")
    else:
        print("❌ Orbit not achieved. Consider training for more episodes or adjusting parameters.")
