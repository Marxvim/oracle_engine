graph LR
A[Begin] --> B{Define binary_search function}
B --> C[Initialize low to 0]
C --> D[Initialize high to len(array) - 1]
D --> E{While low is less than or equal to high}
E --> F[Calculate mid as the floor of (low + high) / 2]
F --> G{If array[mid] is equal to target}
G --> H[Return mid]
G --> I{else if array[mid] is less than target}
I --> J[Set low to mid + 1]
I --> K{else}
K --> L[Set high to mid - 1]
E --> M[If not met, return -1]
M --> N[End]