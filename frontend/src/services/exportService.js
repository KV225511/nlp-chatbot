/**
 * Export conversation history and mood analytics to PDF
 */
export async function exportChatToPDF(messages, moodHistory) {
    if (!messages || messages.length === 0) {
        alert('No messages to export yet. Start chatting first!');
        return;
    }

    try {
        // Loaded on demand so the PDF library is not part of the initial page load
        const { jsPDF } = await import('jspdf');
        const doc = new jsPDF();
        let yPos = 22;
        const margin = 16;
        const pageWidth = doc.internal.pageSize.getWidth();
        const maxWidth = pageWidth - 2 * margin;

        // Header Title
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(20);
        doc.setTextColor(99, 102, 241);
        doc.text('CosmosBot — Mission Transcript', margin, yPos);
        yPos += 7;

        // Subtitle
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(110, 110, 150);
        doc.text(`Generated: ${new Date().toLocaleString()} | Deep Learning Space Chatbot`, margin, yPos);
        yPos += 5;
        doc.text(`Total Messages: ${messages.length} | Model: CNN + BiGRU + Attention`, margin, yPos);
        yPos += 8;

        // Divider
        doc.setDrawColor(210, 210, 235);
        doc.setLineWidth(0.5);
        doc.line(margin, yPos, pageWidth - margin, yPos);
        yPos += 10;

        // Messages list
        messages.forEach((msg) => {
            if (yPos > 265) {
                doc.addPage();
                yPos = 20;
            }

            const isUser = msg.sender === 'user';
            const icon = isUser ? '[You]' : '[CosmosBot]';

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9.5);
            doc.setTextColor(isUser ? 79 : 99, isUser ? 70 : 102, isUser ? 229 : 241);
            doc.text(`${icon} ${msg.timestamp || ''}`, margin, yPos);

            if (!isUser && msg.source === 'knowledge_base' && typeof msg.confidence === 'number') {
                const confPercent = Math.round(msg.confidence * 100);
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(8.5);
                doc.setTextColor(130, 130, 160);
                doc.text(`(Knowledge base: ${msg.intent || 'unknown'} - ${confPercent}% match)`, margin + 55, yPos);
            }

            if (!isUser && msg.source === 'web') {
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(8.5);
                doc.setTextColor(130, 130, 160);
                doc.text('(Answered from the web)', margin + 55, yPos);
            }

            if (isUser && msg.sentiment) {
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(8.5);
                doc.setTextColor(130, 130, 160);
                doc.text(`[Mood: ${msg.sentiment.label || 'neutral'}]`, margin + 35, yPos);
            }

            yPos += 5;

            // Message text body
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10);
            doc.setTextColor(30, 30, 50);

            const cleanText = (msg.text || '')
                .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
                .trim();

            const lines = doc.splitTextToSize(cleanText, maxWidth);
            lines.forEach((line) => {
                if (yPos > 275) {
                    doc.addPage();
                    yPos = 20;
                }
                doc.text(line, margin, yPos);
                yPos += 5;
            });

            (msg.sources || []).forEach((item) => {
                if (yPos > 275) {
                    doc.addPage();
                    yPos = 20;
                }
                doc.setFontSize(8.5);
                doc.setTextColor(99, 102, 241);
                doc.textWithLink(`Source: ${item.provider} - ${item.title}`, margin, yPos, { url: item.url });
                yPos += 5;
            });

            yPos += 4;
        });

        // Mood Summary Section
        if (moodHistory && moodHistory.length > 0) {
            if (yPos > 240) {
                doc.addPage();
                yPos = 20;
            }

            yPos += 6;
            doc.setDrawColor(210, 210, 235);
            doc.line(margin, yPos, pageWidth - margin, yPos);
            yPos += 9;

            doc.setFont('helvetica', 'bold');
            doc.setFontSize(13);
            doc.setTextColor(99, 102, 241);
            doc.text('Sentiment & Mood Summary', margin, yPos);
            yPos += 7;

            const avg = moodHistory.reduce((acc, curr) => acc + (curr.compound || 0), 0) / moodHistory.length;
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(10);
            doc.setTextColor(50, 50, 70);
            doc.text(`Total Interacted Mood Points: ${moodHistory.length}`, margin, yPos);
            yPos += 5;
            doc.text(`Overall Average Sentiment Score: ${avg.toFixed(3)} (${avg > 0.05 ? 'Positive' : avg < -0.05 ? 'Negative' : 'Neutral'})`, margin, yPos);
        }

        // Footer pagination
        const totalPages = doc.internal.getNumberOfPages();
        for (let i = 1; i <= totalPages; i++) {
            doc.setPage(i);
            doc.setFontSize(8);
            doc.setTextColor(150, 150, 180);
            doc.text(`CosmosBot AI Explorer | Page ${i} of ${totalPages}`, pageWidth / 2, 288, { align: 'center' });
        }

        const dateStr = new Date().toISOString().slice(0, 10);
        doc.save(`CosmosBot_Chat_${dateStr}.pdf`);
    } catch (err) {
        console.error('PDF export error:', err);
        alert('Could not export PDF. Please check console.');
    }
}
