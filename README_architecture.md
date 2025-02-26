# Architecture Visualizer

This Python script generates visualizations of the Customer Engagement System architecture, showing both the current monolithic structure and the proposed microservices architecture.

## Features

- Generates a visual representation of the current monolithic architecture
- Generates a visual representation of the proposed microservices architecture
- Creates a side-by-side comparison of both architectures
- Includes annotations highlighting key issues and benefits

## Requirements

The script requires the following Python packages:
- matplotlib
- networkx
- numpy
- Pillow (PIL)

## Installation

1. Ensure you have Python 3.6+ installed on your system
2. Install the required packages:

```bash
pip install matplotlib networkx numpy pillow
```

## Usage

Simply run the script:

```bash
python architecture_visualizer.py
```

## Output

The script generates three PNG files:
- `monolithic_architecture.png` - Current state architecture diagram
- `microservices_architecture.png` - Proposed future state architecture diagram
- `architecture_comparison.png` - Side-by-side comparison of both architectures

## Architecture Details

### Current Monolithic Architecture
The current architecture shows tightly coupled components with the following issues:
- Heavy coupling between UI and business logic
- Inconsistent error handling
- Scaling challenges
- Limited separation of concerns

### Proposed Microservices Architecture
The proposed architecture introduces:
- API Gateway for unified access
- Independent microservices (Auth, Customer Profile, Analytics, etc.)
- Separate databases for different domains
- Clear separation of concerns

### Implementation Timeline
The implementation is divided into three phases:
1. **Phase 1 (0-3 months)**: Database query optimization & error handling standardization
2. **Phase 2 (3-6 months)**: Begin transition with Analytics & Reporting services
3. **Phase 3 (6+ months)**: Complete migration to microservices architecture

## Customization

You can modify the script to:
- Add or remove components
- Change the layout of the diagrams
- Adjust colors and styling
- Add additional annotations or explanations