import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import axios from "axios";
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js";
import { 
  Rocket, 
  Target, 
  Globe, 
  ChartLineUp, 
  Lightning, 
  Check, 
  User, 
  SignOut, 
  MagnifyingGlass,
  ArrowRight,
  CreditCard,
  Buildings,
  Phone,
  Envelope,
  Link as LinkIcon,
  WarningCircle,
  Sparkle,
  CaretDown,
  X
} from "@phosphor-icons/react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PAYPAL_CLIENT_ID = process.env.REACT_APP_PAYPAL_CLIENT_ID;

// Auth Context
const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (e) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password }, { withCredentials: true });
    setUser(response.data);
    return response.data;
  };

  const register = async (email, password, name) => {
    const response = await axios.post(`${API}/auth/register`, { email, password, name }, { withCredentials: true });
    setUser(response.data);
    return response.data;
  };

  const logout = async () => {
    await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    setUser(null);
  };

  const refreshUser = async () => {
    await checkAuth();
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Protected Route
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#0055FF] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Landing Page
const LandingPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target weight="bold" className="w-8 h-8 text-[#0055FF]" />
            <span className="font-outfit text-xl font-bold tracking-tight">LeadGen Pro</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-[#A1A1AA] hover:text-white transition-colors">Features</a>
            <a href="#pricing" className="text-[#A1A1AA] hover:text-white transition-colors">Pricing</a>
            <a href="#how-it-works" className="text-[#A1A1AA] hover:text-white transition-colors">How It Works</a>
          </nav>
          <div className="flex items-center gap-4">
            {user ? (
              <button 
                onClick={() => navigate('/dashboard')}
                className="px-5 py-2.5 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-medium transition-all duration-200 hover:-translate-y-0.5"
                data-testid="go-to-dashboard-btn"
              >
                Dashboard
              </button>
            ) : (
              <>
                <button 
                  onClick={() => navigate('/login')}
                  className="px-4 py-2 text-white hover:text-[#0055FF] transition-colors"
                  data-testid="login-btn"
                >
                  Login
                </button>
                <button 
                  onClick={() => navigate('/signup')}
                  className="px-5 py-2.5 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-medium transition-all duration-200 hover:-translate-y-0.5"
                  data-testid="get-started-btn"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6 overflow-hidden">
        <div 
          className="absolute inset-0 z-0"
          style={{
            backgroundImage: `linear-gradient(to bottom, rgba(5,5,5,0.3), rgba(5,5,5,0.9)), url('https://images.pexels.com/photos/30547584/pexels-photo-30547584.jpeg')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="max-w-3xl">
            <span className="mono-label text-[#0055FF] mb-4 block">FOR WEB DEVELOPERS</span>
            <h1 className="font-outfit text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-tight mb-6">
              Real Business Leads<br />
              <span className="text-[#0055FF]">Ready to Buy</span>
            </h1>
            <p className="text-xl text-[#A1A1AA] mb-8 max-w-xl">
              Access businesses worldwide that need websites. No website, outdated designs, poor SEO — we find them all, with AI-powered sales pitches ready to go.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={() => navigate('/signup')}
                className="px-8 py-4 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold text-lg transition-all duration-200 hover:-translate-y-1 pulse-glow flex items-center justify-center gap-2"
                data-testid="hero-cta-btn"
              >
                Start Getting Leads <ArrowRight weight="bold" />
              </button>
              <a 
                href="#how-it-works"
                className="px-8 py-4 border border-white/20 hover:border-white/40 text-white rounded-md font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-2"
              >
                See How It Works
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 px-6 border-y border-white/10 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "1M+", label: "Businesses Indexed" },
            { value: "150+", label: "Countries Covered" },
            { value: "97%", label: "Lead Accuracy" },
            { value: "24/7", label: "AI Analysis" }
          ].map((stat, i) => (
            <div key={i} className="text-center">
              <div className="font-outfit text-4xl font-bold text-white mb-2">{stat.value}</div>
              <div className="mono-label text-[#A1A1AA]">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="mono-label text-[#0055FF] mb-4 block">FEATURES</span>
            <h2 className="font-outfit text-4xl sm:text-5xl font-bold tracking-tight mb-4">
              Everything You Need to Close Deals
            </h2>
            <p className="text-[#A1A1AA] text-lg max-w-2xl mx-auto">
              Our platform combines Google Maps data, AI analysis, and smart lead distribution to give you the best prospects.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Globe, title: "Global Reach", desc: "Leads from businesses worldwide — not limited to one region." },
              { icon: Sparkle, title: "AI Sales Pitches", desc: "GPT-powered pitches and proposals customized for each business." },
              { icon: Target, title: "Smart Detection", desc: "Find businesses with no website, outdated designs, or poor SEO." },
              { icon: Lightning, title: "Instant Access", desc: "350 leads on signup, 200 more with each monthly payment." },
              { icon: ChartLineUp, title: "Unique Leads", desc: "Each lead assigned exclusively to you — no competition." },
              { icon: MagnifyingGlass, title: "Business Search", desc: "Search any business and get instant AI analysis." }
            ].map((feature, i) => (
              <div 
                key={i} 
                className="p-8 bg-[#121212] border border-white/10 rounded-md hover:border-[#0055FF]/50 transition-all duration-200"
              >
                <feature.icon weight="duotone" className="w-10 h-10 text-[#0055FF] mb-4" />
                <h3 className="font-outfit text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-[#A1A1AA]">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-6 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="mono-label text-[#0055FF] mb-4 block">HOW IT WORKS</span>
            <h2 className="font-outfit text-4xl sm:text-5xl font-bold tracking-tight">
              From Signup to Sales in 3 Steps
            </h2>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: "01", title: "Sign Up & Pay", desc: "Create your account and pay the $35 signup fee via PayPal. Get instant access to 250 qualified leads." },
              { step: "02", title: "Browse Leads", desc: "Each lead includes business details, website URL (if any), AI-generated pitch, and proposal." },
              { step: "03", title: "Close Deals", desc: "Reach out with our pre-made pitches. Need more leads? Pay $10 for 100 additional leads anytime." }
            ].map((item, i) => (
              <div key={i} className="relative">
                <div className="mono-label text-6xl font-bold text-[#0055FF]/20 mb-4">{item.step}</div>
                <h3 className="font-outfit text-2xl font-semibold mb-3">{item.title}</h3>
                <p className="text-[#A1A1AA]">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="mono-label text-[#0055FF] mb-4 block">PRICING</span>
            <h2 className="font-outfit text-4xl sm:text-5xl font-bold tracking-tight mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-[#A1A1AA] text-lg">
              Try before you commit - start with our tester pack
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {/* Tester Package */}
            <div className="p-8 bg-[#121212] border border-[#00E676] rounded-md relative overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="mono-label text-xs bg-[#00E676] text-black px-3 py-1 rounded">TRY FIRST</span>
              </div>
              <h3 className="font-outfit text-2xl font-bold mb-2">Tester Pack</h3>
              <div className="flex items-baseline gap-2 mb-4">
                <span className="font-outfit text-5xl font-bold">$8</span>
                <span className="text-[#A1A1AA]">one-time</span>
              </div>
              <ul className="space-y-3 mb-8">
                {[
                  "50 real business leads",
                  "Verify quality first",
                  "Phone, email & website",
                  "AI-generated pitches",
                  "No commitment"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-[#A1A1AA]">
                    <Check weight="bold" className="w-5 h-5 text-[#00E676]" />
                    {item}
                  </li>
                ))}
              </ul>
              <button 
                onClick={() => navigate('/signup?plan=tester')}
                className="w-full py-4 bg-[#00E676] hover:bg-[#00C853] text-black rounded-md font-semibold transition-all duration-200"
                data-testid="pricing-tester-btn"
              >
                Try 50 Leads for $8
              </button>
            </div>

            {/* Signup Package */}
            <div className="p-8 bg-[#121212] border-2 border-[#0055FF] rounded-md relative overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="mono-label text-xs bg-[#0055FF] text-white px-3 py-1 rounded">BEST VALUE</span>
              </div>
              <h3 className="font-outfit text-2xl font-bold mb-2">Full Access</h3>
              <div className="flex items-baseline gap-2 mb-4">
                <span className="font-outfit text-5xl font-bold">$35</span>
                <span className="text-[#A1A1AA]">one-time</span>
              </div>
              <ul className="space-y-3 mb-8">
                {[
                  "250 qualified leads",
                  "5x more than tester",
                  "Full business details",
                  "AI sales pitches",
                  "Lifetime access"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-[#A1A1AA]">
                    <Check weight="bold" className="w-5 h-5 text-[#00E676]" />
                    {item}
                  </li>
                ))}
              </ul>
              <button 
                onClick={() => navigate('/signup?plan=full')}
                className="w-full py-4 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold transition-all duration-200"
                data-testid="pricing-signup-btn"
              >
                Get 250 Leads for $35
              </button>
            </div>

            {/* Refill Package */}
            <div className="p-8 bg-[#121212] border border-white/10 rounded-md">
              <h3 className="font-outfit text-2xl font-bold mb-2">Lead Refill</h3>
              <div className="flex items-baseline gap-2 mb-4">
                <span className="font-outfit text-5xl font-bold">$10</span>
                <span className="text-[#A1A1AA]">per pack</span>
              </div>
              <ul className="space-y-3 mb-8">
                {[
                  "100 new leads",
                  "Fresh businesses",
                  "New industries",
                  "Pay when needed",
                  "No subscription"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-[#A1A1AA]">
                    <Check weight="bold" className="w-5 h-5 text-[#00E676]" />
                    {item}
                  </li>
                ))}
              </ul>
              <button 
                onClick={() => navigate('/signup')}
                className="w-full py-4 border border-white/20 hover:border-white/40 text-white rounded-md font-semibold transition-all duration-200"
                data-testid="pricing-refill-btn"
              >
                After Signup/Tester
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 bg-[#0055FF]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-outfit text-4xl sm:text-5xl font-bold tracking-tight mb-6">
            Not Sure? Try 50 Leads for $8
          </h2>
          <p className="text-xl text-white/80 mb-8">
            See the quality for yourself. Real businesses, real contact info, real opportunities.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button 
              onClick={() => navigate('/signup?plan=tester')}
              className="px-10 py-4 bg-[#00E676] text-black rounded-md font-bold text-lg hover:bg-[#00C853] transition-all duration-200 hover:-translate-y-1"
              data-testid="cta-tester-btn"
            >
              Try 50 Leads - $8
            </button>
            <button 
              onClick={() => navigate('/signup?plan=full')}
              className="px-10 py-4 bg-white text-[#0055FF] rounded-md font-bold text-lg hover:bg-white/90 transition-all duration-200 hover:-translate-y-1"
              data-testid="cta-signup-btn"
            >
              Get 250 Leads - $35
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Target weight="bold" className="w-6 h-6 text-[#0055FF]" />
            <span className="font-outfit font-bold">LeadGen Pro</span>
          </div>
          <p className="text-[#A1A1AA] text-sm">
            © 2026 LeadGen Pro. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) navigate('/dashboard');
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Target weight="bold" className="w-10 h-10 text-[#0055FF]" />
            <span className="font-outfit text-2xl font-bold">LeadGen Pro</span>
          </div>
          <h1 className="font-outfit text-3xl font-bold mb-2">Welcome Back</h1>
          <p className="text-[#A1A1AA]">Sign in to access your leads</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-md text-red-400 text-sm" data-testid="login-error">
              {error}
            </div>
          )}
          
          <div>
            <label className="block mono-label text-[#A1A1AA] mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none focus:ring-2 focus:ring-[#0055FF]/20 transition-all"
              placeholder="you@example.com"
              required
              data-testid="login-email-input"
            />
          </div>
          
          <div>
            <label className="block mono-label text-[#A1A1AA] mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none focus:ring-2 focus:ring-[#0055FF]/20 transition-all"
              placeholder="••••••••"
              required
              data-testid="login-password-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-4 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="login-submit-btn"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-center mt-6 text-[#A1A1AA]">
          Don't have an account?{" "}
          <button onClick={() => navigate('/signup')} className="text-[#0055FF] hover:underline" data-testid="go-to-signup-link">
            Sign up
          </button>
        </p>
        
        <button onClick={() => navigate('/')} className="w-full mt-4 text-center text-[#A1A1AA] hover:text-white transition-colors">
          ← Back to home
        </button>
      </div>
    </div>
  );
};

// Signup Page with PayPal
const SignupPage = () => {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState("full"); // 'tester' or 'full'
  const { register, user, refreshUser } = useAuth();
  const navigate = useNavigate();

  // Get plan from URL
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const plan = params.get('plan');
    if (plan === 'tester') {
      setSelectedPlan('tester');
    } else {
      setSelectedPlan('full');
    }
  }, []);

  useEffect(() => {
    if (user && (user.subscription_status === 'active' || user.subscription_status === 'tester')) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const planDetails = {
    tester: { price: "8.00", leads: 50, label: "Tester Pack", type: "tester" },
    full: { price: "35.00", leads: 250, label: "Full Access", type: "signup" }
  };

  const currentPlan = planDetails[selectedPlan];

  const handleRegister = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, password, name);
      setStep(2);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSuccess = async (orderID) => {
    try {
      await axios.post(`${API}/payments/process`, {
        payment_type: currentPlan.type,
        paypal_order_id: orderID,
        amount: parseFloat(currentPlan.price)
      }, { withCredentials: true });
      await refreshUser();
      navigate('/dashboard');
    } catch (err) {
      setError('Payment processing failed. Please contact support.');
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Target weight="bold" className="w-10 h-10 text-[#0055FF]" />
            <span className="font-outfit text-2xl font-bold">LeadGen Pro</span>
          </div>
          <h1 className="font-outfit text-3xl font-bold mb-2">
            {step === 1 ? "Create Account" : "Complete Payment"}
          </h1>
          <p className="text-[#A1A1AA]">
            {step === 1 
              ? `Get ${currentPlan.leads} leads for just $${currentPlan.price}` 
              : `Pay $${currentPlan.price} to get your ${currentPlan.leads} leads`}
          </p>
        </div>

        {/* Plan Selector */}
        {step === 1 && (
          <div className="flex gap-2 mb-6">
            <button
              type="button"
              onClick={() => setSelectedPlan('tester')}
              className={`flex-1 py-3 px-4 rounded-md font-semibold transition-all ${
                selectedPlan === 'tester' 
                  ? 'bg-[#00E676] text-black' 
                  : 'bg-[#121212] text-[#A1A1AA] border border-white/10'
              }`}
            >
              Tester $8
            </button>
            <button
              type="button"
              onClick={() => setSelectedPlan('full')}
              className={`flex-1 py-3 px-4 rounded-md font-semibold transition-all ${
                selectedPlan === 'full' 
                  ? 'bg-[#0055FF] text-white' 
                  : 'bg-[#121212] text-[#A1A1AA] border border-white/10'
              }`}
            >
              Full $35
            </button>
          </div>
        )}

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${step >= 1 ? 'bg-[#0055FF] text-white' : 'bg-[#121212] text-[#A1A1AA]'}`}>
            1
          </div>
          <div className={`w-16 h-0.5 ${step >= 2 ? 'bg-[#0055FF]' : 'bg-[#121212]'}`} />
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${step >= 2 ? 'bg-[#0055FF] text-white' : 'bg-[#121212] text-[#A1A1AA]'}`}>
            2
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-md text-red-400 text-sm mb-4" data-testid="signup-error">
            {error}
          </div>
        )}

        {step === 1 ? (
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block mono-label text-[#A1A1AA] mb-2">Full Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none focus:ring-2 focus:ring-[#0055FF]/20 transition-all"
                placeholder="John Doe"
                required
                data-testid="signup-name-input"
              />
            </div>
            
            <div>
              <label className="block mono-label text-[#A1A1AA] mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none focus:ring-2 focus:ring-[#0055FF]/20 transition-all"
                placeholder="you@example.com"
                required
                data-testid="signup-email-input"
              />
            </div>
            
            <div>
              <label className="block mono-label text-[#A1A1AA] mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none focus:ring-2 focus:ring-[#0055FF]/20 transition-all"
                placeholder="••••••••"
                required
                minLength={6}
                data-testid="signup-password-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold transition-all duration-200 disabled:opacity-50"
              data-testid="signup-continue-btn"
            >
              {loading ? "Creating account..." : "Continue to Payment"}
            </button>
          </form>
        ) : (
          <div className="space-y-6">
            <div className="p-6 bg-[#121212] border border-white/10 rounded-md">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[#A1A1AA]">{currentPlan.label}</span>
                <span className="font-outfit text-2xl font-bold">${currentPlan.price}</span>
              </div>
              <ul className="space-y-2 text-sm text-[#A1A1AA]">
                <li className="flex items-center gap-2">
                  <Check weight="bold" className="w-4 h-4 text-[#00E676]" />
                  {currentPlan.leads} qualified leads
                </li>
                <li className="flex items-center gap-2">
                  <Check weight="bold" className="w-4 h-4 text-[#00E676]" />
                  AI-generated pitches
                </li>
                <li className="flex items-center gap-2">
                  <Check weight="bold" className="w-4 h-4 text-[#00E676]" />
                  Lifetime access
                </li>
              </ul>
            </div>

            <PayPalScriptProvider options={{ clientId: PAYPAL_CLIENT_ID, currency: "USD" }}>
              <PayPalButtons
                style={{ layout: "vertical", color: "blue", shape: "rect" }}
                createOrder={(data, actions) => {
                  return actions.order.create({
                    purchase_units: [{
                      amount: { value: currentPlan.price },
                      description: `LeadGen Pro - ${currentPlan.label} (${currentPlan.leads} Leads)`
                    }]
                  });
                }}
                onApprove={async (data, actions) => {
                  const order = await actions.order.capture();
                  await handlePaymentSuccess(order.id);
                }}
                onError={(err) => {
                  setError('Payment failed. Please try again.');
                }}
                data-testid="paypal-buttons"
              />
            </PayPalScriptProvider>

            <button
              onClick={() => setStep(1)}
              className="w-full text-center text-[#A1A1AA] hover:text-white transition-colors"
            >
              ← Back to account details
            </button>
          </div>
        )}

        <p className="text-center mt-6 text-[#A1A1AA]">
          Already have an account?{" "}
          <button onClick={() => navigate('/login')} className="text-[#0055FF] hover:underline">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};

// Dashboard Page
const DashboardPage = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [showPayment, setShowPayment] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLocation, setSearchLocation] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [leadsRes, statsRes] = await Promise.all([
        axios.get(`${API}/leads`, { withCredentials: true }),
        axios.get(`${API}/stats`, { withCredentials: true })
      ]);
      setLeads(leadsRes.data.leads);
      setStats(statsRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateLeads = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(`${API}/leads/generate`, {}, { withCredentials: true });
      setLeads(prev => [...response.data.leads, ...prev]);
      await refreshUser();
      await fetchData();
    } catch (err) {
      if (err.response?.status === 400) {
        setShowPayment(true);
      }
    } finally {
      setGenerating(false);
    }
  };

const updateLeadStatus = async (leadId, status) => {
    try {
      await axios.patch(`${API}/leads/${leadId}/status`, { status }, { withCredentials: true });
      setLeads(prev => prev.map(l => l.id === leadId ? { ...l, lead_status: status } : l));
      if (selectedLead?.id === leadId) {
        setSelectedLead(prev => ({ ...prev, lead_status: status }));
      }
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const handleRefillPayment = async (orderID) => {
    try {
      await axios.post(`${API}/payments/process`, {
        payment_type: 'refill',
        paypal_order_id: orderID,
        amount: 10.00
      }, { withCredentials: true });
      await refreshUser();
      setShowPayment(false);
      await generateLeads();
    } catch (err) {
      console.error('Payment failed', err);
    }
  };

  const searchBusiness = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    setSearchResults([]);
    try {
      const response = await axios.post(`${API}/leads/search`, {
        query: searchQuery,
        location: searchLocation || null
      }, { withCredentials: true });
      setSearchResults(response.data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#0055FF] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505]">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target weight="bold" className="w-8 h-8 text-[#0055FF]" />
            <span className="font-outfit text-xl font-bold tracking-tight">LeadGen Pro</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-[#121212] rounded-md border border-white/10">
              <User weight="fill" className="w-5 h-5 text-[#0055FF]" />
              <span className="text-sm">{user?.name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 hover:bg-white/10 rounded-md transition-colors"
              data-testid="logout-btn"
            >
              <SignOut weight="bold" className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total Leads", value: stats?.total_leads || 0, icon: Target },
            { label: "Leads Remaining", value: user?.leads_remaining || 0, icon: Lightning },
            { label: "With Website", value: stats?.leads_with_website || 0, icon: Globe },
            { label: "No Website", value: stats?.leads_without_website || 0, icon: WarningCircle }
          ].map((stat, i) => (
            <div key={i} className="p-6 bg-[#121212] border border-white/10 rounded-md">
              <div className="flex items-center gap-3 mb-2">
                <stat.icon weight="duotone" className="w-6 h-6 text-[#0055FF]" />
                <span className="mono-label text-[#A1A1AA]">{stat.label}</span>
              </div>
              <div className="font-outfit text-3xl font-bold">{stat.value}</div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <button
            onClick={generateLeads}
            disabled={generating || (user?.leads_remaining || 0) <= 0}
            className="flex-1 py-4 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            data-testid="generate-leads-btn"
          >
            {generating ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generating Leads...
              </>
            ) : (
              <>
                <Rocket weight="fill" /> Generate New Leads
              </>
            )}
          </button>
          
          <button
            onClick={() => setShowPayment(true)}
            className="flex-1 py-4 border border-[#0055FF] text-[#0055FF] hover:bg-[#0055FF] hover:text-white rounded-md font-semibold transition-all duration-200 flex items-center justify-center gap-2"
            data-testid="buy-more-leads-btn"
          >
            <CreditCard weight="fill" /> Get 100 More Leads - $10
          </button>
        </div>

        {/* Business Search */}
        <div className="mb-8 p-6 bg-[#121212] border border-white/10 rounded-md">
          <h3 className="font-outfit text-xl font-semibold mb-4 flex items-center gap-2">
            <MagnifyingGlass weight="bold" className="text-[#0055FF]" />
            Search Any Business
          </h3>
          <form onSubmit={searchBusiness} className="flex flex-col md:flex-row gap-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Business name or type (e.g., 'Pizza Restaurant')"
              className="flex-1 px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none"
              data-testid="search-query-input"
            />
            <input
              type="text"
              value={searchLocation}
              onChange={(e) => setSearchLocation(e.target.value)}
              placeholder="Location (optional)"
              className="md:w-48 px-4 py-3 bg-[#0A0A0A] border border-white/20 rounded-md text-white focus:border-[#0055FF] focus:outline-none"
              data-testid="search-location-input"
            />
            <button
              type="submit"
              disabled={searching || !searchQuery.trim()}
              className="px-6 py-3 bg-[#0055FF] hover:bg-[#3377FF] text-white rounded-md font-semibold transition-all disabled:opacity-50"
              data-testid="search-submit-btn"
            >
              {searching ? "Searching..." : "Search"}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="mt-6 space-y-4">
              <h4 className="mono-label text-[#A1A1AA]">Search Results ({searchResults.length})</h4>
              {searchResults.map((result, i) => (
                <div key={i} className="p-4 bg-[#0A0A0A] border border-white/10 rounded-md">
                  <div className="flex justify-between items-start mb-2">
                    <h5 className="font-outfit text-lg font-semibold">{result.business_name}</h5>
                    {result.has_website ? (
                      <span className="mono-label text-xs bg-[#00E676]/20 text-[#00E676] px-2 py-1 rounded">Has Website</span>
                    ) : (
                      <span className="mono-label text-xs bg-[#FF3B30]/20 text-[#FF3B30] px-2 py-1 rounded">No Website</span>
                    )}
                  </div>
                  <p className="text-[#A1A1AA] text-sm mb-2">{result.address}</p>
                  {result.website && (
                    <a href={result.website} target="_blank" rel="noopener noreferrer" className="text-[#0055FF] text-sm hover:underline flex items-center gap-1">
                      <LinkIcon weight="bold" className="w-4 h-4" /> {result.website}
                    </a>
                  )}
                  <div className="mt-3 p-3 bg-[#121212] rounded border border-white/5">
                    <p className="text-sm text-[#A1A1AA] mb-2"><strong className="text-white">AI Pitch:</strong> {result.ai_pitch}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Leads List */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-outfit text-2xl font-semibold">Your Leads</h3>
          </div>
          {/* Status Tabs */}
          <div className="flex gap-2 mb-6 flex-wrap">
            {[
              { key: "all", label: "All" },
              { key: "new", label: "New" },
              { key: "viewed", label: "Viewed" },
              { key: "contacted", label: "Contacted" },
              { key: "interested", label: "Interested" },
              { key: "closed", label: "Closed" },
              { key: "not_interested", label: "Not Interested" }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? 'bg-[#0055FF] text-white'
                    : 'bg-[#121212] text-[#A1A1AA] border border-white/10 hover:border-white/30'
                }`}
              >
                {tab.label} ({leads.filter(l => tab.key === 'all' ? true : (l.lead_status || 'new') === tab.key).length})
              </button>
            ))}
          </div>
          
          {leads.filter(l => activeTab === 'all' ? true : (l.lead_status || 'new') === activeTab).length === 0 ? (
            <div className="text-center py-16 bg-[#121212] border border-white/10 rounded-md">
              <Target weight="duotone" className="w-16 h-16 text-[#0055FF] mx-auto mb-4" />
              <h4 className="font-outfit text-xl font-semibold mb-2">No Leads Yet</h4>
              <p className="text-[#A1A1AA] mb-6">Click "Generate New Leads" to get your first batch of business leads</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {leads.filter(l => activeTab === 'all' ? true : (l.lead_status || 'new') === activeTab).map((lead, i) => (
                <div 
                  key={lead.id || i}
                  className="p-6 bg-[#121212] border border-white/10 rounded-md hover:border-[#0055FF]/30 transition-all cursor-pointer"
                  onClick={() => setSelectedLead(lead)}
                  data-testid={`lead-card-${i}`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Buildings weight="duotone" className="w-6 h-6 text-[#0055FF]" />
                        <h4 className="font-outfit text-lg font-semibold">{lead.business_name}</h4>
                        {lead.is_fake && (
                          <span className="mono-label text-xs bg-[#FFEA00]/20 text-[#FFEA00] px-2 py-0.5 rounded">SAMPLE</span>
                        )}
                      </div>
                      <p className="text-[#A1A1AA] text-sm mb-2">{lead.address}</p>
                      <div className="flex flex-wrap gap-4 text-sm">
                        {lead.phone && (
                          <span className="flex items-center gap-1 text-[#A1A1AA]">
                            <Phone weight="fill" className="w-4 h-4" /> {lead.phone}
                          </span>
                        )}
                        {lead.email && (
                          <a 
                            href={`mailto:${lead.email}`}
                            className="flex items-center gap-1 text-[#00E676] hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Envelope weight="fill" className="w-4 h-4" /> {lead.email}
                          </a>
                        )}
                        {lead.website ? (
                          <a 
                            href={lead.website} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="flex items-center gap-1 text-[#0055FF] hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <LinkIcon weight="bold" className="w-4 h-4" /> View Website
                          </a>
                        ) : (
                          <span className="flex items-center gap-1 text-[#FF3B30]">
                            <WarningCircle weight="fill" className="w-4 h-4" /> No Website
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                      <select
                        value={lead.lead_status || 'new'}
                        onChange={e => updateLeadStatus(lead.id, e.target.value)}
                        className="px-3 py-1.5 bg-[#0A0A0A] border border-white/20 rounded-md text-sm text-white focus:border-[#0055FF] focus:outline-none"
                      >
                        <option value="new">New</option>
                        <option value="viewed">Viewed</option>
                        <option value="contacted">Contacted</option>
                        <option value="interested">Interested</option>
                        <option value="closed">Closed</option>
                        <option value="not_interested">Not Interested</option>
                      </select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Lead Detail Modal */}
      {selectedLead && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80" onClick={() => setSelectedLead(null)}>
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-[#121212] border border-white/10 rounded-md" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-white/10 flex items-center justify-between sticky top-0 bg-[#121212]">
              <h3 className="font-outfit text-xl font-semibold">{selectedLead.business_name}</h3>
              <button onClick={() => setSelectedLead(null)} className="p-2 hover:bg-white/10 rounded-md transition-colors">
                <X weight="bold" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-6">
              {/* Business Info */}
              <div>
                <h4 className="mono-label text-[#0055FF] mb-3">Business Details</h4>
                <div className="space-y-2 text-[#A1A1AA]">
                  <p><strong className="text-white">Address:</strong> {selectedLead.address}</p>
                  {selectedLead.phone && <p><strong className="text-white">Phone:</strong> {selectedLead.phone}</p>}
                  {selectedLead.email && (
                    <p>
                      <strong className="text-white">Email:</strong>{" "}
                      <a href={`mailto:${selectedLead.email}`} className="text-[#00E676] hover:underline">
                        {selectedLead.email}
                      </a>
                    </p>
                  )}
                  {selectedLead.website ? (
                    <p>
                      <strong className="text-white">Website:</strong>{" "}
                      <a href={selectedLead.website} target="_blank" rel="noopener noreferrer" className="text-[#0055FF] hover:underline">
                        {selectedLead.website}
                      </a>
                    </p>
                  ) : (
                    <p><strong className="text-white">Website:</strong> <span className="text-[#FF3B30]">None - Great opportunity!</span></p>
                  )}
                </div>
              </div>

              {/* Issues */}
              <div>
                <h4 className="mono-label text-[#0055FF] mb-3">Website Issues Detected</h4>
                <ul className="space-y-2">
                  {selectedLead.website_issues?.map((issue, i) => (
                    <li key={i} className="flex items-center gap-2 text-[#A1A1AA]">
                      <WarningCircle weight="fill" className="w-4 h-4 text-[#FFEA00]" />
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>

              {/* AI Pitch */}
              <div>
                <h4 className="mono-label text-[#0055FF] mb-3">AI-Generated Sales Pitch</h4>
                <div className="p-4 bg-[#0A0A0A] border border-white/10 rounded-md">
                  <p className="text-white leading-relaxed">{selectedLead.ai_pitch}</p>
                </div>
              </div>

              {/* AI Proposal */}
              <div>
                <h4 className="mono-label text-[#0055FF] mb-3">AI-Generated Proposal</h4>
                <div className="p-4 bg-[#0A0A0A] border border-white/10 rounded-md">
                  <p className="text-white whitespace-pre-line leading-relaxed">{selectedLead.ai_proposal}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80" onClick={() => setShowPayment(false)}>
          <div className="w-full max-w-md bg-[#121212] border border-white/10 rounded-md" onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-white/10 flex items-center justify-between">
              <h3 className="font-outfit text-xl font-semibold">Get More Leads</h3>
              <button onClick={() => setShowPayment(false)} className="p-2 hover:bg-white/10 rounded-md transition-colors">
                <X weight="bold" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-6 p-4 bg-[#0A0A0A] border border-white/10 rounded-md">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[#A1A1AA]">Lead Refill Pack</span>
                  <span className="font-outfit text-2xl font-bold">$10</span>
                </div>
                <p className="text-sm text-[#A1A1AA]">Get 100 new qualified business leads</p>
              </div>

              <PayPalScriptProvider options={{ clientId: PAYPAL_CLIENT_ID, currency: "USD" }}>
                <PayPalButtons
                  style={{ layout: "vertical", color: "blue", shape: "rect" }}
                  createOrder={(data, actions) => {
                    return actions.order.create({
                      purchase_units: [{
                        amount: { value: "10.00" },
                        description: "LeadGen Pro - Lead Refill (200 Leads)"
                      }]
                    });
                  }}
                  onApprove={async (data, actions) => {
                    const order = await actions.order.capture();
                    await handleRefillPayment(order.id);
                  }}
                  data-testid="refill-paypal-buttons"
                />
              </PayPalScriptProvider>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;
