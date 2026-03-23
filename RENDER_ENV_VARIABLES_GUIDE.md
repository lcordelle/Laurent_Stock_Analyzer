# 🔧 Render Environment Variables - Step-by-Step Guide

## 🎯 Goal: Set Python Version to 3.11.9 in Render Dashboard

---

## 📋 Step-by-Step Instructions

### STEP 1: Go to Your Render Dashboard

1. **Open**: https://dashboard.render.com
2. **Log in** if needed
3. You should see your services listed

---

### STEP 2: Open Your Service

1. **Find**: Your service named `stock-analyzer` (or whatever you named it)
2. **Click** on the service name
3. You'll see the service details page

---

### STEP 3: Go to Settings Tab

1. **Look for tabs** at the top of the page:
   - Logs | Metrics | Events | **Settings** | etc.
2. **Click**: **"Settings"** tab
3. You'll see the settings page

---

### STEP 4: Find Environment Variables Section

1. **Scroll down** on the Settings page
2. **Look for**: **"Environment Variables"** section
   - It might be near the bottom
   - Or in an "Advanced" section
3. You'll see:
   - A list of existing environment variables (if any)
   - An **"Add Environment Variable"** button or **"+"** button

---

### STEP 5: Add Python Version Variable

1. **Click**: **"Add Environment Variable"** or **"+"** button
2. **Two fields will appear**:
   - **Key** (or Name)
   - **Value**

3. **Fill in the fields**:
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.11.9`

4. **Click**: **"Save Changes"** or **"Add"** button

---

### STEP 6: Save and Redeploy

1. **Scroll to bottom** of Settings page
2. **Click**: **"Save Changes"** (if there's a save button)
3. **Go to**: **"Manual Deploy"** tab (or look for deploy options)
4. **Click**: **"Deploy latest commit"** or **"Clear build cache & deploy"**
5. **Wait**: 5-10 minutes for new build

---

## 📊 Visual Guide - What You'll See

### Screen 1: Service Dashboard
```
┌─────────────────────────────────────┐
│  stock-analyzer                     │
│  Status: Live / Building            │
├─────────────────────────────────────┤
│  [Logs] [Metrics] [Events] [Settings]│
│                                     │
│  Service Details...                 │
└─────────────────────────────────────┘
```

### Screen 2: Settings Tab
```
┌─────────────────────────────────────┐
│  Settings                            │
├─────────────────────────────────────┤
│                                     │
│  Service Name: stock-analyzer       │
│  Region: Oregon (US West)           │
│  Branch: main                       │
│                                     │
│  ... (other settings) ...           │
│                                     │
│  Environment Variables              │
│  ┌─────────────────────────────┐   │
│  │ Key              Value       │   │
│  │ (empty - no vars yet)        │   │
│  └─────────────────────────────┘   │
│  [+ Add Environment Variable]       │
│                                     │
│  [Save Changes]                     │
└─────────────────────────────────────┘
```

### Screen 3: Adding Environment Variable
```
┌─────────────────────────────────────┐
│  Add Environment Variable           │
├─────────────────────────────────────┤
│                                     │
│  Key:   [PYTHON_VERSION        ]   │
│  Value: [3.11.9                ]   │
│                                     │
│  [Add] [Cancel]                     │
└─────────────────────────────────────┘
```

### Screen 4: After Adding
```
┌─────────────────────────────────────┐
│  Environment Variables              │
├─────────────────────────────────────┤
│  Key              Value             │
│  PYTHON_VERSION   3.11.9            │
│                                     │
│  [+ Add Environment Variable]       │
└─────────────────────────────────────┘
```

---

## 🔍 Alternative Locations

If you don't see "Environment Variables" in Settings:

### Option A: Look in "Environment" Section
- Some Render versions have an "Environment" tab
- Click "Environment" → Add variable there

### Option B: Look in "Advanced" Section
- Click "Advanced" to expand
- Environment Variables might be there

### Option C: Look in Service Configuration
- Some versions show it during service creation
- You might need to edit the service configuration

---

## ✅ Verification

After adding the variable:

1. **Check**: The variable appears in the list
   - Key: `PYTHON_VERSION`
   - Value: `3.11.9`

2. **Deploy**: Click "Manual Deploy" → "Deploy latest commit"

3. **Check Build Logs**: 
   - Should see: `Python 3.11.9` instead of `3.13`
   - Build should succeed

---

## 🚀 Quick Steps Summary

1. ✅ Dashboard → Your Service
2. ✅ Click "Settings" tab
3. ✅ Scroll to "Environment Variables"
4. ✅ Click "Add Environment Variable"
5. ✅ Key: `PYTHON_VERSION`
6. ✅ Value: `3.11.9`
7. ✅ Save
8. ✅ Deploy latest commit

---

## 📝 Exact Values to Enter

**Key** (exactly as shown):
```
PYTHON_VERSION
```

**Value** (exactly as shown):
```
3.11.9
```

**⚠️ Important**: 
- Use capital letters for the key
- Use the exact version number: `3.11.9`
- No spaces before or after

---

## 🔄 After Setting the Variable

1. **Save** the environment variable
2. **Go to**: "Manual Deploy" tab
3. **Click**: "Clear build cache & deploy" (recommended)
4. **Wait**: 5-10 minutes
5. **Check logs**: Should see Python 3.11.9

---

## ❓ Still Can't Find It?

If you can't find Environment Variables:

1. **Try**: Click "Edit" or "Configure" on your service
2. **Look for**: "Environment" or "Env Vars" section
3. **Alternative**: Delete and recreate the service with the variable set

---

## 🎯 What This Does

Setting `PYTHON_VERSION=3.11.9` tells Render to:
- Use Python 3.11.9 instead of default (3.13)
- This is compatible with pandas 2.1.4
- Build should succeed

---

**Follow these steps and your build should work! 🚀**


