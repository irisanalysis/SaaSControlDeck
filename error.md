## 一、

Runtime Error


Error: [object Object]

Call Stack
1

Hide 1 ignore-listed frame(s)
onUnhandledRejection
node_modules/next/src/client/components/errors/use-error-handler.ts (122:13)

## 二、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

Call Stack
8

Hide 8 ignore-listed frame(s)
createConsoleError
node_modules/next/src/client/components/errors/console-error.ts (18:35)
handleConsoleError
node_modules/next/src/client/components/errors/use-error-handler.ts (30:31)
console.error
node_modules/next/src/client/components/globals/intercept-console-error.ts (32:27)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3867:17)
enqueueConcurrentHookUpdate
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3820:14)
dispatchSetStateInternal
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8121:18)
dispatchSetState
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8081:7)
<unknown>
node_modules/next/src/client/components/react-dev-overlay/ui/components/errors/dev-tools-indicator/use-minimum-loading-time-multiple.tsx (53:13)

## 三、

src/hooks/use-data-preview.ts (42:5) @ useDataPreview.useCallback[resetPreview]


  40 |
  41 |   const resetPreview = useCallback(() => {
> 42 |     setState({
     |     ^
  43 |       preview: null,
  44 |       qualityChecks: [],
  45 |       loading: false,
Call Stack
12

Show 8 ignore-listed frame(s)
useDataPreview.useCallback[resetPreview]
src/hooks/use-data-preview.ts (42:5)
useDataPreview.useEffect
src/hooks/use-data-preview.ts (171:7)
DataManagementContent
src/app/data-management/page.tsx (41:9)
DataManagementPage
src/app/data-management/page.tsx (186:7)

## 四、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

Call Stack
12

Hide 11 ignore-listed frame(s)
createConsoleError
node_modules/next/src/client/components/errors/console-error.ts (18:35)
handleConsoleError
node_modules/next/src/client/components/errors/use-error-handler.ts (30:31)
console.error
node_modules/next/src/client/components/globals/intercept-console-error.ts (32:27)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3867:17)
enqueueConcurrentRenderForLane
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3824:14)
forceStoreRerender
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (7263:18)
<unknown>
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (7249:41)
<unknown>
node_modules/next/src/client/dev/dev-build-indicator/internal/initialize.ts (28:37)
Array.forEach
<anonymous> (0:0)
_devbuildindicator.devBuildIndicator.show
node_modules/next/src/client/dev/dev-build-indicator/internal/initialize.ts (28:15)
handleDevBuildIndicatorHmrEvents
node_modules/next/src/client/dev/dev-build-indicator/internal/handle-dev-build-indicator-hmr-events.ts (20:27)
WebSocket.handler
node_modules/next/src/client/components/react-dev-overlay/app/hot-reloader-client.tsx (604:41)

## 五、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

src/app/layout.tsx (44:9) @ RootLayout


  42 |           </SidebarProvider>
  43 |         </AuthProvider>
> 44 |         <Toaster />
     |         ^
  45 |       </body>
  46 |     </html>
  47 |   );
Call Stack
52

Show 48 ignore-listed frame(s)
Array.map
<anonymous> (0:0)
Array.map
<anonymous> (0:0)
li
<anonymous> (0:0)
RootLayout
src/app/layout.tsx (44:9)

## 六、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

src/hooks/use-data-preview.ts (63:7) @ useDataPreview.useCallback[loadPreview]


  61 |       ]);
  62 |
> 63 |       setState(prev => ({
     |       ^
  64 |         ...prev,
  65 |         preview,
  66 |         qualityChecks,
Call Stack
8

Hide 7 ignore-listed frame(s)
createConsoleError
node_modules/next/src/client/components/errors/console-error.ts (18:35)
handleConsoleError
node_modules/next/src/client/components/errors/use-error-handler.ts (30:31)
console.error
node_modules/next/src/client/components/globals/intercept-console-error.ts (32:27)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3867:17)
enqueueConcurrentHookUpdate
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3820:14)
dispatchSetStateInternal
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8121:18)
dispatchSetState
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8081:7)
useDataPreview.useCallback[loadPreview]
src/hooks/use-data-preview.ts (63:7)

## 七、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

src/hooks/use-data-preview.ts (55:5) @ useDataPreview.useCallback[loadPreview]


  53 |     }
  54 |
> 55 |     setState(prev => ({ ...prev, loading: true, error: null }));
     |     ^
  56 |
  57 |     try {
  58 |       const [preview, qualityChecks] = await Promise.all([
Call Stack
12

Hide 8 ignore-listed frame(s)
createConsoleError
node_modules/next/src/client/components/errors/console-error.ts (18:35)
handleConsoleError
node_modules/next/src/client/components/errors/use-error-handler.ts (30:31)
console.error
node_modules/next/src/client/components/globals/intercept-console-error.ts (32:27)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3867:17)
enqueueConcurrentHookUpdate
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3820:14)
dispatchSetStateInternal
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8121:18)
dispatchSetState
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8081:7)
useDataPreview.useCallback[loadPreview]
src/hooks/use-data-preview.ts (55:5)
useDataPreview.useEffect
src/hooks/use-data-preview.ts (169:7)
DataManagementContent
src/app/data-management/page.tsx (41:9)
DataManagementPage
src/app/data-management/page.tsx (186:7)
ClientPageRoot
node_modules/next/src/client/components/client-page.tsx (60:12)

## 八、

Console Error


Maximum update depth exceeded. This can happen when a component calls setState inside useEffect, but useEffect either doesn't have a dependency array, or one of the dependencies changes on every render.

src/hooks/use-toast.ts (139:5) @ <unknown>


  137 |   memoryState = reducer(memoryState, action)
  138 |   listeners.forEach((listener) => {
> 139 |     listener(memoryState)
      |     ^
  140 |   })
  141 | }
  142 |
Call Stack
16

Hide 11 ignore-listed frame(s)
createConsoleError
node_modules/next/src/client/components/errors/console-error.ts (18:35)
handleConsoleError
node_modules/next/src/client/components/errors/use-error-handler.ts (30:31)
console.error
node_modules/next/src/client/components/globals/intercept-console-error.ts (32:27)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3867:17)
enqueueConcurrentHookUpdate
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3820:14)
dispatchSetStateInternal
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8121:18)
dispatchSetState
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8081:7)
<unknown>
src/hooks/use-toast.ts (139:5)
Array.forEach
<anonymous> (0:0)
dispatch
src/hooks/use-toast.ts (138:13)
dismiss
src/hooks/use-toast.ts (153:25)
Object.onOpenChange [as current]
src/hooks/use-toast.ts (162:20)
useControllableState.useCallback[setValue]
node_modules/@radix-ui/react-use-controllable-state/src/use-controllable-state.tsx (56:23)
onClose
node_modules/@radix-ui/react-toast/src/toast.tsx (397:26)
ToastImpl.useCallbackRef[handleClose] [as current]
node_modules/@radix-ui/react-toast/src/toast.tsx (496:7)
useCallbackRef.useMemo
node_modules/@radix-ui/react-use-callback-ref/src/use-callback-ref.tsx (15:56)

## 九、

Runtime Error


Error: Maximum update depth exceeded. This can happen when a component repeatedly calls setState inside componentWillUpdate or componentDidUpdate. React limits the number of nested updates to prevent infinite loops.

Call Stack
6

Hide 6 ignore-listed frame(s)
getRootForUpdatedFiber
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3860:11)
enqueueConcurrentHookUpdate
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (3820:14)
dispatchSetStateInternal
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8121:18)
dispatchSetState
node_modules/next/dist/compiled/react-dom/cjs/react-dom-client.development.js (8081:7)
ToastProvider.useCallback
node_modules/@radix-ui/react-toast/src/toast.tsx (103:48)
ToastImpl.useEffect
node_modules/@radix-ui/react-toast/src/toast.tsx (540:20)