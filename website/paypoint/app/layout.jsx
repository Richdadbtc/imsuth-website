import PayPoint from '../components/paypoint.jsx';
import '../static/paypoint/app.css';
import '../static/paypoint/frontend.css';
import '../static/paypoint/layout-fixes.css';
import '../static/paypoint/target-dashboard.css';
import '../static/paypoint/target-polish.css';
import './next.css';

export const metadata = {
  title: 'IMSUTH PayPoint',
  description: 'IMSUTH hospital revenue management',
  robots: {index:false, follow:false},
  icons: {icon:'/paypoint/images/hospital%20logo.png'},
};
export default function RootLayout({children}) {
  return <html lang="en"><body className="paypoint-static-ui"><PayPoint>{children}</PayPoint></body></html>;
}
