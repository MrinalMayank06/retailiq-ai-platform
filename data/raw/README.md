# Raw Data Folder

This folder stores the source CSV files used by RetailIQ AI Platform.

## Required files
- `product_details.csv`
- `customer_data.csv`
- `order_data.csv`

## Role
These files act as the initial source for:
- data preparation
- feature engineering
- ML training
- support knowledge construction

## Notes
- Do not rename the files unless code references are also updated.
- Curated outputs are generated separately into `data/curated/`.