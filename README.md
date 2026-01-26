# 🛍️ Markaz to Shopify CSV Converter

A powerful web application that scrapes product data from Markaz marketplace and converts it into Shopify-compatible CSV format. Available as both a Streamlit web app and a Vercel serverless API.

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

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Markaz-Products-Cloning
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Run the Streamlit app**
   ```bash
   streamlit run app.py
   ```

   The app will open at `http://localhost:8501`

## 📦 Project Structure

```
Markaz-Products-Cloning/
├── app.py                 # Main Streamlit application
├── api/
│   └── index.py          # Vercel serverless function (API endpoint)
├── requirements.txt       # Python dependencies
├── packages.txt          # OS-level dependencies (for Streamlit Cloud)
├── vercel.json           # Vercel deployment configuration
├── pyproject.toml        # Python project configuration
├── runtime.txt          # Python version specification
├── .vercelignore        # Files to ignore for Vercel
├── .gitignore          # Files to ignore for Git
└── README.md            # This file
```

## 🌐 Deployment Options

### Option 1: Streamlit Community Cloud (Recommended for UI)

**Best for:** Full Streamlit web application with UI

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Sign in with GitHub
   - Click "New app"
   - Select repository and branch
   - Main file: `app.py`
   - Click "Deploy"

**Requirements:**
- ✅ `requirements.txt` (includes streamlit, playwright, pandas)
- ✅ `packages.txt` (system dependencies for Playwright)
- ✅ `app.py` in root directory

**Features:**
- Full Streamlit UI
- Free tier available
- Automatic browser installation
- WebSocket support

### Option 2: Vercel (API Endpoint)

**Best for:** Serverless API endpoint for scraping

1. **Push code to GitHub**

2. **Deploy on Vercel**
   - Visit: https://vercel.com
   - Import GitHub repository
   - Vercel auto-detects Python function

**Configuration:**
- ✅ `vercel.json` configured
- ✅ `api/index.py` as serverless function
- ✅ Minimal dependencies (playwright only)

**Usage:**
```
https://your-app.vercel.app?url=PRODUCT_URL
```

**Features:**
- Fast serverless API
- JSON responses
- Free tier available
- No WebSocket needed

## 📖 Usage

### Using the Streamlit App

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

### Using the Vercel API

**Endpoint:**
```
GET https://your-app.vercel.app?url=PRODUCT_URL
```

**Response:**
```json
{
  "title": "Product Title",
  "description": "Product Description",
  "price": "1500",
  "base_sku": "MZ51500000049KSAA",
  "variants": ["Small", "Medium", "Large"],
  "image_urls": ["https://..."],
  "breadcrumb_items": ["Marketplace", "Men", "Track Suit"],
  "status": "success"
}
```

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

### Breadcrumb Extraction

- Extracts navigation path: `Marketplace / Men / Track Suit`
- Tags: All breadcrumb items (comma-separated)
- Standard Product Type: Second-to-last item
- Filters out: Followers, Products count, Prices

## 🛠️ Technical Details

### Technologies Used

- **Streamlit**: Web application framework
- **Playwright**: Browser automation for scraping JavaScript-rendered content
- **Pandas**: Data manipulation and CSV generation
- **Python 3.12+**: Programming language

### Dependencies

**Python Packages** (`requirements.txt`):
- `streamlit>=1.30.0` - Web framework
- `playwright>=1.40.0` - Browser automation
- `pandas>=2.0.0` - Data manipulation

**System Packages** (`packages.txt` - for Streamlit Cloud):
- Chromium browser dependencies (libnss3, libatk1.0-0, etc.)

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
- For Vercel deployment, browsers are installed at runtime (not during build)

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

4. **Vercel build fails (size limit)**
   - Ensure only `playwright==1.40.0` in requirements.txt
   - Check `.vercelignore` includes all unnecessary files
   - Browsers install at runtime, not during build

5. **Streamlit Cloud build fails**
   - Verify `packages.txt` has all system dependencies
   - Check `requirements.txt` has all Python packages
   - Ensure `app.py` is in root directory

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues or questions, please open an issue on the GitHub repository.

---

**Made with ❤️ for efficient e-commerce data migration**
