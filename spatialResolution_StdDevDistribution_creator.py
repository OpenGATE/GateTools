import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import argparse

# Function to pool the matrix
def pool_matrix(df, N_prime, M_prime):
    # Get the original dimensions
    N, M = df.shape

    # Calculate block sizes
    A = N // N_prime
    B = M // M_prime

    if N % N_prime != 0 or M % M_prime != 0:
        raise ValueError("N and M must be divisible by N' and M' respectively.")

    # Reshape into blocks and calculate mean for each block
    pooled = (
        df.values.reshape(N_prime, A, M_prime, B)  # Reshape into blocks
        .mean(axis=(1, 3))  # Average over the blocks
    )

    # Convert back to DataFrame for better readability
    return pd.DataFrame(pooled)

# Function to write matrix with coordinates
def write_matrix_with_coordinates(df, lenX, lenY, outputfile="output.txt"):
    # Get number of rows and columns from the matrix shape
    rows, cols = df.shape
    
    # Generate coordinate arrays for X and Y
    x_coords = np.linspace(-lenX/2, lenX/2, cols)
    y_coords = np.linspace(-lenY/2, lenY/2, rows)

    # Open file to write the output
    with open(outputfile, "w") as file:
        # Write header row with x coordinates
        file.write(" ".join([f"{x:.2f}" for x in x_coords]) + "\n")
        
        # Write each row with y coordinates and corresponding matrix data
        for y, row_data in zip(y_coords, df.values):
            file.write(f"{y:.2f}" + " " + " ".join(map(str, row_data)) + "\n")
    
    return y_coords, df

# Main function that will be executed when the script runs
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process matrix with coordinate output.")
    
    # Define the flags and their corresponding arguments
    parser.add_argument('-i', '--inputfile', type=str, required=True, help="Input file path")
    parser.add_argument('-o', '--outputfile', type=str, required=True, help="Output file path")
    parser.add_argument('-n', '--NumRows', type=int, required=True, help="Number of rows of the final matrix.")
    parser.add_argument('-m', '--NumColumns', type=int, required=True, help="Number of columns of the final matrix.")
    parser.add_argument('-x', '--lenX', type=float, required=True, help="Length of X axis")
    parser.add_argument('-y', '--lenY', type=float, required=True, help="Length of Y axis")

    args = parser.parse_args()
    
    # Read the input file into a DataFrame
    df = pd.read_csv(args.inputfile, sep='\s+', header=None, index_col=None)

    # Pool the matrix if necessary
    pooled_df = pool_matrix(df, args.N_prime, args.M_prime)

    # Write the matrix with coordinates to the output file
    write_matrix_with_coordinates(pooled_df, lenX=args.lenX, lenY=args.lenY, outputfile=args.outputfile)

if __name__ == "__main__":
    main()
