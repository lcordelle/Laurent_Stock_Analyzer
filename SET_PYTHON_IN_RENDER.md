# ⚡ Quick Guide: Set Python Version in Render

## 🎯 Quick Steps

1. **Go to**: https://dashboard.render.com
2. **Click**: Your service `stock-analyzer`
3. **Click**: **"Settings"** tab
4. **Scroll to**: **"Environment Variables"** section
5. **Click**: **"+ Add Environment Variable"** or **"Add"** button
6. **Enter**:
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.11.9`
7. **Click**: **"Save"** or **"Add"**
8. **Go to**: **"Manual Deploy"** tab
9. **Click**: **"Clear build cache & deploy"**
10. **Wait**: 5-10 minutes

---

## 📋 Exact Values

```
Key:   PYTHON_VERSION
Value: 3.11.9
```

---

## ✅ After Setting

- Build logs should show: `Python 3.11.9`
- pandas 2.1.4 should install successfully
- Build should complete

---

**That's it! 🚀**

