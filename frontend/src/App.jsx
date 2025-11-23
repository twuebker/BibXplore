import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, BookOpen, Sparkles } from 'lucide-react';

export default function App() {
    const [showBook, setShowBook] = useState(true);
    const [query, setQuery] = useState('');
    const [books, setBooks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => {
            setShowBook(false);
        }, 1500);
        return () => clearTimeout(timer);
    }, []);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);

        try {
            const response = await fetch('http://127.0.0.1:5000/get_books', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            setBooks(data.books || []);
        } catch (error) {
            console.error('Search error:', error);
            setBooks([]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ minHeight: '100vh', position: 'relative', overflow: 'hidden' }}>
            {/* Animated Background */}
            <div style={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
                zIndex: -1
            }}>
                {[...Array(20)].map((_, i) => (
                    <motion.div
                        key={i}
                        style={{
                            position: 'absolute',
                            width: '2px',
                            height: '2px',
                            background: '#94a3b8',
                            borderRadius: '50%',
                            top: `${Math.random() * 100}%`,
                            left: `${Math.random() * 100}%`,
                        }}
                        animate={{
                            opacity: [0.2, 0.8, 0.2],
                            scale: [1, 1.5, 1],
                        }}
                        transition={{
                            duration: 1 + Math.random() * 2,
                            repeat: Infinity,
                            delay: Math.random() * 2,
                        }}
                    />
                ))}
            </div>

            {/* Opening Book Animation */}
            <AnimatePresence>
                {showBook && (
                    <motion.div
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        style={{
                            position: 'fixed',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            background: 'rgba(15, 23, 42, 0.95)',
                            zIndex: 100,
                            backdropFilter: 'blur(10px)',
                        }}
                    >
                        <div style={{ position: 'relative', perspective: '1500px' }}>
                            <motion.div
                                initial={{ rotateY: 0 }}
                                animate={{ rotateY: -180 }}
                                transition={{ duration: 1.0, ease: [0.43, 0.13, 0.23, 0.96] }}
                                style={{
                                    width: '200px',
                                    height: '280px',
                                    background: 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    transformStyle: 'preserve-3d',
                                    boxShadow: '0 20px 60px rgba(124, 58, 237, 0.4)',
                                }}
                            >
                                <BookOpen size={80} color="#fff" strokeWidth={1.5} />
                            </motion.div>

                            <motion.div
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 0.5, duration: 0.5 }}
                                style={{
                                    position: 'absolute',
                                    top: '320px',
                                    left: '0',
                                    right: '0',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    gap: '8px',
                                }}
                            >
                                <Sparkles size={20} color="#a78bfa" />
                                <span style={{ color: '#e2e8f0', fontSize: '24px', fontWeight: '300', letterSpacing: '2px' }}>
                  BibXplore
                </span>
                                <Sparkles size={20} color="#a78bfa" />
                            </motion.div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: showBook ? 0 : 1 }}
                transition={{  duration: 0.5 }}
                style={{
                    maxWidth: '1400px',
                    margin: '0 auto',
                    padding: '80px 40px 40px',
                }}
            >
                {/* Header */}
                <motion.div
                    initial={{ y: -30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 1, duration: 0.6 }}
                    style={{ textAlign: 'center', marginBottom: '60px' }}
                >
                    <h1 style={{
                        fontSize: '56px',
                        fontWeight: '700',
                        background: 'linear-gradient(135deg, #a78bfa 0%, #6366f1 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        marginBottom: '16px',
                        letterSpacing: '-1px',
                    }}>
                        BibXplore
                    </h1>
                    <p style={{ color: '#94a3b8', fontSize: '18px', fontWeight: '300' }}>
                        Discover your next reading adventure through intelligent search
                    </p>
                </motion.div>

                {/* Search Bar */}
                <motion.form
                    onSubmit={handleSearch}
                    initial={{ y: 30, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.9, duration: 0.3 }}
                    style={{ marginBottom: '60px' }}
                >
                    <div style={{
                        position: 'relative',
                        maxWidth: '800px',
                        margin: '0 auto',
                    }}>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.9, duration: 0.3 }}
                            style={{
                                position: 'absolute',
                                left: '20px',
                                top: '53%',
                                transform: 'translateY(-47%)',
                                color: '#64748b',
                                pointerEvents: 'none',
                                zIndex: 1,
                            }}
                        >
                            <Search size={22} />
                        </motion.div>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search by theme, author, or details..."
                            style={{
                                width: '100%',
                                padding: '18px 20px 18px 52px',
                                fontSize: '18px',
                                background: 'rgba(30, 41, 59, 0.6)',
                                border: '2px solid rgba(148, 163, 184, 0.2)',
                                borderRadius: '16px',
                                color: '#e2e8f0',
                                outline: 'none',
                                transition: 'all 0.3s ease',
                                backdropFilter: 'blur(10px)',
                            }}
                            onFocus={(e) => {
                                e.target.style.borderColor = '#7c3aed';
                                e.target.style.background = 'rgba(30, 41, 59, 0.8)';
                            }}
                            onBlur={(e) => {
                                e.target.style.borderColor = 'rgba(148, 163, 184, 0.2)';
                                e.target.style.background = 'rgba(30, 41, 59, 0.6)';
                            }}
                        />
                        <motion.button
                            type="submit"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            style={{
                                position: 'absolute',
                                right: '9px',
                                top: '50%',
                                padding: '12px 32px',
                                background: 'linear-gradient(135deg, #7c3aed 0%, #6366f1 100%)',
                                border: 'none',
                                borderRadius: '12px',
                                color: '#fff',
                                fontSize: '16px',
                                fontWeight: '600',
                                cursor: 'pointer',
                                boxShadow: '0 4px 20px rgba(124, 58, 237, 0.3)',
                                transformOrigin: 'center',
                                y: '-50%',
                            }}
                        >
                            Search
                        </motion.button>
                    </div>
                </motion.form>

                {/* Loading State */}
                {loading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        style={{ textAlign: 'center', padding: '60px 0' }}
                    >
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                            style={{
                                width: '60px',
                                height: '60px',
                                border: '4px solid rgba(124, 58, 237, 0.2)',
                                borderTop: '4px solid #7c3aed',
                                borderRadius: '50%',
                                margin: '0 auto 20px',
                            }}
                        />
                        <p style={{ color: '#94a3b8', fontSize: '18px' }}>Searching library...</p>
                    </motion.div>
                )}

                {/* Results */}
                {!loading && searched && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6 }}
                    >
                        {books.length > 0 ? (
                            <>
                                <div style={{
                                    color: '#94a3b8',
                                    fontSize: '16px',
                                    marginBottom: '24px',
                                    textAlign: 'center',
                                }}>
                                    Found {books.length} {books.length === 1 ? 'book' : 'books'}
                                </div>
                                <div style={{
                                    background: 'rgba(30, 41, 59, 0.4)',
                                    borderRadius: '16px',
                                    overflow: 'hidden',
                                    border: '1px solid rgba(148, 163, 184, 0.1)',
                                    backdropFilter: 'blur(10px)',
                                }}>
                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                        <thead>
                                        <tr style={{ background: 'rgba(124, 58, 237, 0.1)' }}>
                                            {['ISBN', 'Title', 'Author', 'Pages', 'Year', 'Language', 'Publisher', 'Subject', 'Genre'].map((header) => (
                                                <th key={header} style={{
                                                    padding: '16px',
                                                    textAlign: 'left',
                                                    color: '#a78bfa',
                                                    fontSize: '14px',
                                                    fontWeight: '600',
                                                    textTransform: 'uppercase',
                                                    letterSpacing: '0.5px',
                                                }}>
                                                    {header}
                                                </th>
                                            ))}
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {books.map((book, index) => (
                                            <motion.tr
                                                key={index}
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: index * 0.05 }}
                                                style={{
                                                    borderTop: '1px solid rgba(148, 163, 184, 0.1)',
                                                    transition: 'background 0.2s ease',
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.background = 'rgba(124, 58, 237, 0.05)';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.background = 'transparent';
                                                }}
                                            >
                                                {book.map((cell, cellIndex) => (
                                                    <td key={cellIndex} style={{
                                                        padding: '16px',
                                                        color: cellIndex === 1 ? '#e2e8f0' : '#94a3b8',
                                                        fontSize: '14px',
                                                        fontWeight: cellIndex === 1 ? '500' : '400',
                                                    }}>
                                                        {cell}
                                                    </td>
                                                ))}
                                            </motion.tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            </>
                        ) : (
                            <div style={{
                                textAlign: 'center',
                                padding: '60px 20px',
                                background: 'rgba(30, 41, 59, 0.4)',
                                borderRadius: '16px',
                                border: '1px solid rgba(148, 163, 184, 0.1)',
                            }}>
                                <BookOpen size={48} color="#64748b" style={{ margin: '0 auto 16px' }} />
                                <p style={{ color: '#94a3b8', fontSize: '18px' }}>
                                    No books found. Try a different search term.
                                </p>
                            </div>
                        )}
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
}
