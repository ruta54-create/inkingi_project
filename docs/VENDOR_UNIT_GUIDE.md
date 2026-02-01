# Vendor Unit Guide - Custom Measurement Units

## 🎯 Overview

Vendors can now input custom measurement units when adding or editing products, providing flexibility for different types of wood products and crafts.

## ✅ **New Features**

### **Custom Unit Input**
- **Text Input Field**: Replace dropdown with flexible text input
- **Autocomplete Suggestions**: Built-in suggestions for common units
- **Quick Selection Buttons**: One-click buttons for popular units
- **Validation**: Automatic cleaning and validation of unit names

### **Suggested Units**

#### **Common Wood Product Units:**
- `pcs` - Pieces (individual items)
- `meter` - Per Meter (linear measurement)
- `sqm` - Square Meter (area measurement)
- `cbm` - Cubic Meter (volume measurement)
- `kg` - Kilogram (weight)
- `bundle` - Bundle (grouped items)
- `set` - Set (complete collection)

#### **Additional Options:**
- `pair` - Pair (two items)
- `dozen` - Dozen (12 items)
- `ft` - Feet
- `inch` - Inch
- `cm` - Centimeter
- `liter` - Liter
- `board` - Board
- `plank` - Plank

## 🚀 **How to Use**

### **Adding Products**
1. Navigate to "Add Product" page
2. In the "Unit of Measurement" field:
   - **Type directly**: Enter your custom unit (e.g., "board_feet", "linear_meter")
   - **Use autocomplete**: Start typing and select from suggestions
   - **Quick buttons**: Click on common unit buttons for instant selection

### **Examples of Custom Units**
- `board_feet` - For lumber measurements
- `linear_meter` - For long wood pieces
- `square_foot` - For panels and sheets
- `cubic_inch` - For small carved items
- `per_piece` - For individual crafted items
- `per_log` - For raw wood logs
- `per_slab` - For wood slabs

### **Best Practices**

#### **Unit Naming Guidelines:**
- Use lowercase letters
- Replace spaces with underscores (e.g., `board_feet` not `board feet`)
- Keep it short and descriptive
- Use standard abbreviations when possible

#### **Consistency:**
- Use the same unit format across similar products
- Be specific about what the unit represents
- Consider your customers' understanding

## 🎨 **User Interface Features**

### **Smart Input Field**
- **Autocomplete**: Dropdown suggestions as you type
- **Validation**: Automatic cleaning of special characters
- **Length Limit**: Maximum 50 characters
- **Help Text**: Clear instructions and examples

### **Quick Selection Buttons**
- **One-Click Selection**: Popular units available as buttons
- **Visual Feedback**: Selected button highlights temporarily
- **Smart Highlighting**: Buttons highlight when typing matches

### **Real-Time Validation**
- **Input Cleaning**: Removes special characters automatically
- **Format Standardization**: Converts spaces to underscores
- **Error Prevention**: Clear validation messages

## 📋 **Technical Details**

### **Database Changes**
- Unit field increased to 50 characters
- Removed dropdown constraints
- Added help text for guidance

### **Form Validation**
- Required field validation
- Length limit enforcement
- Character cleaning and normalization
- Duplicate prevention

### **Backward Compatibility**
- Existing products maintain their current units
- Migration preserves all existing data
- No disruption to current listings

## 💡 **Tips for Vendors**

### **Choose Appropriate Units**
- **Furniture**: Use `pcs` for individual pieces
- **Lumber**: Use `meter`, `board_feet`, or `linear_meter`
- **Panels**: Use `sqm` or `square_foot`
- **Carved Items**: Use `pcs` or specific descriptive units
- **Raw Materials**: Use `kg`, `cbm`, or `bundle`

### **Customer Clarity**
- Choose units your customers understand
- Be consistent across similar products
- Use standard measurements when possible
- Consider international customers (metric vs imperial)

### **Inventory Management**
- Align units with your actual inventory tracking
- Consider how you measure and count stock
- Use units that make pricing clear

## 🔧 **Troubleshooting**

### **Common Issues**
- **Unit too long**: Keep under 50 characters
- **Special characters**: System automatically removes them
- **Spaces**: Automatically converted to underscores
- **Empty field**: Unit is required for all products

### **Support**
If you encounter issues with the unit system:
1. Check the help text below the input field
2. Try using suggested units first
3. Contact support if validation errors persist

## 🎉 **Benefits**

### **For Vendors**
- **Flexibility**: Use any measurement unit that fits your products
- **Accuracy**: Precise representation of your inventory
- **Professional**: Clear, standardized product listings
- **Efficiency**: Quick selection options speed up product entry

### **For Customers**
- **Clarity**: Better understanding of product measurements
- **Consistency**: Standardized unit formats across the platform
- **Trust**: Professional, detailed product information

The new custom unit system provides the flexibility vendors need while maintaining a professional, user-friendly experience for customers.