# Troubleshooting Blank White Screen

If you're seeing a blank white screen, follow these steps:

## 1. Check Browser Console
Open Developer Tools (F12) and check the Console tab for errors.

## 2. Check Network Tab
Look for failed requests, especially:
- CSS files not loading
- JavaScript files not loading
- API requests failing

## 3. Verify Dependencies
```bash
cd frontend
npm install
```

## 4. Check if Vite is Running
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## 5. Common Issues

### Issue: CORS Errors
**Solution:** Make sure backend has CORS enabled and is running on port 8000

### Issue: Module Not Found
**Solution:** Run `npm install` in the frontend directory

### Issue: Port Already in Use
**Solution:** Change the port in `vite.config.ts` or kill the process using port 5173

### Issue: TypeScript Errors
**Solution:** Check `tsconfig.json` and ensure all types are installed

## 6. Test Minimal Version

If the full app doesn't work, try the minimal version:

1. Temporarily replace `App.tsx` content with:
```tsx
export default function App() {
  return <div style={{padding: '20px', background: '#000', color: '#fff'}}>App Works!</div>;
}
```

2. If this shows, the issue is in a component
3. If this doesn't show, the issue is in main.tsx or index.html

## 7. Clear Cache
- Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Clear browser cache
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

## 8. Check Environment Variables
Make sure `.env` file exists (if needed) with:
```
VITE_API_BASE_URL=http://localhost:8000/api
```
