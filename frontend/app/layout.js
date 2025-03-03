import { Inter } from 'next/font/google';
import './globals.css';
import { ClerkProvider } from '@clerk/nextjs';
import Providers from './providers';
const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'PaseAI',
  description:
    'ParseAI: Your AI Assitant. Powered by OpenAI, it parses large python codebases, providing instant insights, code suggestions, and learning resources',
};

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang='en'>
        <body className={inter.className}>
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
