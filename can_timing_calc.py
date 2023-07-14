##Calulation script for CAN timings.

"""
BRP (Baud Rate Prescaler): 2
PRSEG (Propagation Segment): 4
PHSEG1 (Phase Segment 1): 8
PHSEG2 (Phase Segment 2): 5

The actual baud rate with this configuration is approximately 75.925 kbps, 
and the sample point is at approximately 72.22% of the total bit time. 
This is as close as we can get given the constraints of the CAN controller and 
the desired baud rate.

when setting these values in your MCP2515 CAN controller, 
you will need to subtract 1 from each of them because they are represented as 
value−1 in the register. For example, a BRP of 2 should be set as 1 in the CNF1 
register.

CNF1 = BRP - 1 = 2 - 1 = 1
CNF2 = ((PRSEG - 1) << 3) | ((PHSEG1 - 1) << 6) | (1 << 7) = ((4 - 1) << 3) | ((8 - 1) << 6) | (1 << 7) = 0xB3
CNF3 = PHSEG2 - 1 = 5 - 1 = 4


mcp2515.setRegister(MCP_CNF1, 0x01);
mcp2515.setRegister(MCP_CNF2, 0xB3);
mcp2515.setRegister(MCP_CNF3, 0x04);


"""




# Define the maximum and minimum values for BRP, PRSEG, PHSEG1, and PHSEG2
BRP_min, BRP_max = 1, 64
PRSEG_min, PRSEG_max = 1, 8
PHSEG1_min, PHSEG1_max = 1, 8
PHSEG2_min, PHSEG2_max = 1, 8

# Oscillator frequency
F_OSC = 8e6  # 8 MHz
# F_OSC = 16e6  # 16 MHz
# F_OSC = 12e6  # 12 MHz


# Desired baud rate
target_baud_rate = 75e3  # 75 kbps

# Desired sample point
target_sample_point = 75  # 75%

# Initialize the best solution with a high error
best_solution = None
best_baud_rate_error = float('inf')
best_sample_point_error = float('inf')

# Iterate over all possible values
for BRP in range(BRP_min, BRP_max+1):
    for PRSEG in range(PRSEG_min, PRSEG_max+1):
        for PHSEG1 in range(PHSEG1_min, PHSEG1_max+1):
            for PHSEG2 in range(PHSEG2_min, PHSEG2_max+1):
                # Calculate the time quantum, the bit time, the baud rate, and the sample point
                TQ = 2 * (BRP + 1) / F_OSC
                T_BIT = (1 + PRSEG + PHSEG1 + PHSEG2) * TQ
                baud_rate = 1 / T_BIT
                sample_point = (1 + PRSEG + PHSEG1) / (1 + PRSEG + PHSEG1 + PHSEG2) * 100
                # Calculate the errors
                baud_rate_error = abs(baud_rate - target_baud_rate)
                sample_point_error = abs(sample_point - target_sample_point)
                # If this solution is better than the best solution so far, update the best solution
                if baud_rate_error < best_baud_rate_error or (baud_rate_error == best_baud_rate_error and sample_point_error < best_sample_point_error):
                    best_solution = (BRP, PRSEG, PHSEG1, PHSEG2)
                    best_baud_rate_error = baud_rate_error
                    best_sample_point_error = sample_point_error

print(best_solution, best_baud_rate_error, best_sample_point_error)
