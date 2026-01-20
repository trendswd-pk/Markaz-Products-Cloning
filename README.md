# 🛍️ Markaz to Shopify CSV Converter

A Streamlit web application that scrapes product data from Markaz marketplace and converts it into Shopify-compatible CSV format. This tool automates the process of extracting product information, handling variants, and formatting data for easy import into Shopify.

## ✨ Features

- **Web Scraping**: Uses Playwright to scrape product data from Markaz product pages, handling JavaScript-rendered content
- **Product Data Extraction**:
  - Product Title, Description, Price, and Images
  - Product Code (Base SKU)
  - Product Variants (Size/Color) with automatic detection
  - Breadcrumb Navigation (Categories and Tags)
- **Shopify CSV Generation**:
  - All 48 required Shopify columns in exact order
  - Automatic Handle generation: `[slugified-title]-[product-code]`
  - Custom pricing engine (adds 500 if price < 2000, else adds 1000)
  - Variant handling with unique SKUs
  - Multiple images support
  - Fixed inventory quantity (50 units)
- **Bulk Processing**: Add multiple products to a list and export all at once
- **User-Friendly Interface**: Clean Streamlit UI with product preview and CSV download

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Markaz-Products-Cloning
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

## 📖 Usage

### Running the Application

1. **Activate the virtual environment** (if not already activated)
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

   Or use the provided shell script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

### Using the Application

1. **Add Products**:
   - Paste a Markaz product URL in the input field
   - Click "Add to List" to scrape and add the product
   - Repeat for multiple products

2. **Review Products**:
   - View all added products in the expandable list
   - Check extracted data: Title, SKU, Variants, Price, Images
   - Remove products if needed

3. **Download CSV**:
   - Click "Download Shopify CSV" to export all products
   - The CSV file will be ready for direct import into Shopify

## 📋 CSV Format Details

The generated CSV includes all 48 Shopify-required columns:

- **Product Information**: Handle, Title, Body (HTML), Vendor, Standard Product Type
- **Variants**: Option1 Name/Value, Variant SKU, Variant Price, Variant Inventory Qty
- **Pricing**: Cost per item (original price), Variant Price (with markup)
- **Images**: Image Src, Image Position, Image Alt Text
- **SEO**: SEO Title, SEO Description
- **Tags**: Comma-separated breadcrumb categories
- **Inventory**: Fixed at 50 units, Inventory Policy: 'continue'

### Pricing Logic

- If original price < 2000: Add 500
- If original price >= 2000: Add 1000
- Original price stored in "Cost per item"
- Calculated price stored in "Variant Price"

### Variant Handling

- Automatically detects Size or Color variants
- Creates separate CSV rows for each variant
- Variant SKU format: `[Base SKU]-[Variant Value]`
- Example: `MZ51500000049KSAA-Small`, `MZ51500000049KSAA-Medium`

## 🛠️ Technical Details

### Technologies Used

- **Streamlit**: Web application framework
- **Playwright**: Browser automation for scraping JavaScript-rendered content
- **Pandas**: Data manipulation and CSV generation
- **BeautifulSoup**: HTML parsing (backup)
- **Requests**: HTTP requests (backup)

### Project Structure

```
Markaz-Products-Cloning/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── run.sh                # Shell script to run the app
├── README.md             # This file
└── venv/                 # Virtual environment (created during setup)
```

## 🔧 Configuration

### Customization Options

You can modify the following in `app.py`:

- **Pricing Markup**: Edit the pricing logic in `create_shopify_row()` function
- **Inventory Quantity**: Change the fixed inventory value (currently 50)
- **Vendor Name**: Update the vendor name (currently 'Markaz')
- **Handle Format**: Modify `generate_unique_handle()` function

## 📝 Example

**Input**: Markaz Product URL
```
https://www.shop.markaz.app/explore/product/Grey%20Mobile%20Phone%20Holder/579974
```

**Output**: Shopify CSV with:
- Handle: `grey-mobile-phone-holder-mz51100000317afts`
- Tags: `Marketplace, Beauty&Fashion, Cosmetics, Personal Care`
- Standard Product Type: `Personal Care`
- Variants: `Small, Medium, Large, X-Large` (if available)
- Images: All product images with positions

## ⚠️ Notes

- The scraper uses headless browser automation, so scraping may take a few seconds per product
- Ensure you have a stable internet connection
- Some products may not have variants (will default to 'Default Title')
- Breadcrumb extraction requires the page to have proper navigation structure

## 🐛 Troubleshooting

### Common Issues

1. **Playwright not installed**
   ```bash
   playwright install chromium
   ```

2. **Import errors**
   - Ensure virtual environment is activated
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Scraping fails**
   - Check if the URL is valid
   - Verify internet connection
   - The website structure may have changed

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues or questions, please open an issue on the GitHub repository.

---

**Made with ❤️ for efficient e-commerce data migration**
