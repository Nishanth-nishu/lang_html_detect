import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from annotator.tagger import annotate

user_input = """本研究的关键结果表明该模型在不同条件下具有稳定性，并且方法可以推广到更复杂的数据场景。作者还补充说明：这个结论需要在更大样本上进一步验证。 في هذا الجزء، يوضح الباحث أن النتائج الأولية مشجعة، لكن هناك حاجة إلى تجارب إضافية قبل اعتماد الاستนتاج النهائي. இந்த பகுதியில், ஆய்வின் முக்கிய கருத்துக்களாக தெரிகின்ற விளக்கப்படுகிறது, மேலும் அதன் அடிப்படையில் முடிவுகள் அதிகரிக்கப்படுகின்றன.

Sample 2:

English: Apple, River, Mountain Spanish: Manzana, Río, Montaña Japanese (Kanji/Kana): リンゴ (Ringo), 川 (Kawa), 山 (Yama) Arabic: تفاحة (Tuffaha), نهر (Nahr), جبل (Jabal) Hindi: सेब (Seb), नदी (Nadi), पहाड़ (Pahaad)

Sample 3:
The global community is more connected than ever. In Paris, people say 'C'est la vie' when facing challenges, while in Tokyo, the concept of 'Ikigai' (生き甲斐) drives their purpose. Many travelers find that 'La dolce vita' in Italy is a universal dream. However, regardless of where you are, the sentiment of 'Home is where the heart is' remains a constant truth across every Cultura and Sprache.

Sample 4:
The methods section includes equation, figure, table, and conclusion. Inline words appear as Merci, Gracias, Danke, 谢谢, شكرا, நன்றி. We validated the result successfully. El resultado es estable. Le résultat es stable.
Sample 5:
References, bibliography, and glossary are complete in this chapter. Test tokens: capitolo, ciao, salut, hallo, こんにちは, 안녕하세요, नमस्ते. The final release package is ready. Esta frase está en español. Ceci est une phrase en français.
Sample 6.
.השלום מתחיל מבפנים (Peace starts from within.)


Sample 7.
Nel libro, l’introduzione presenta lo sfondo e un breve riassunto con parole chiave; nel primo capitolo compaiono anche titolo, sottোটitolo, nota e conclusione. La sezione finale include conclusioni, bibliografia, glossario e Ulteriore lettura, mentre in appendice troviamo allegato, appendice e appendici con materiale extra. Per la parte tecnica, il testo usa definizione, definizioni, ipotesi, metodo e metodi, con passaggi matematici come Eq., Eqn., equazione, formula, espressione, lemma, teorema, corollario, proposta e prova. I risultati sono mostrati con fig., figura, tabella, grafico, diagramma, schema e casella di testo, con fonte verificata per ogni elemento. Nel blocco metadata compaiono abbreviazione, abbreviazioni, nomenclatura, classificazione, codici, indice dei termini, Indice chimico, indice materiale, fonte indice e Termine thesaurus. Il contenuto copre geochimica, nuova astronomia e biologia molecolare e cellulare, con riferimientos a materiale, materiali, relazione, reazione, regressione e risultati.

Sample 8. 
The fintech market is growing rapidly, especially in Latin America. Muchos clientes confían en aplicaciones móviles para pagos diarios. Analysts note that “trust” and “seguridad” are the most important factors influencing adoption.
Sample 9.
Customer loyalty is not just about discounts; c’est aussi une question de confiance. In India, कई उपयोगकर्ता डिजिटल वॉलेट का उपयोग करते हैं for everyday transactions. This blend of cultures shows how fintech adapts globally.
Sample 10.
Monthly volume metrics are critical for forecasting. Viele Banken nutzen KI-Modelle to detect fraud. Meanwhile, தமிழ்நாட்டில் பலர் UPI payments prefer செய்கிறார்கள், showing regional adoption trends.

Sample 11.
In this single mixed-English test paragraph, we greet the world with one word from many major languages: hello, hola, bonjour, olá, ciao, hallo, привет, 你好, こんにちは, 안녕하세요, नमस्ते, নমস্কার, ਸਤ ਸ੍ਰੀ ਅকাল, నమస్తే, नमस्कार, வணக்கம், سلام, مرحبا, merhaba, xinchào, สวัสดี, မင်္ဂလာပါ, សួស្តី, ສະບາຍດີ, ආයුබෝවன், નમස්તે, ನಮસ્කාර, നമസ്കാരം, ନମସ୍କାର, নমস্কাৰ, γεια, שלום, jambo, sannu, bawo, ndewo, salaan, sawubona, molo, hej, hei, moi, dia, helo, kaixo, salut, cześć, ahoj, szia, bok, zdravo, živjo, labas, sveiki, tere, përshëndetje, здраво, გამარჯობა, բარև, salam, сәлем, salom, салам, салом, сайн, silav, kiaora, talofa, malo, bula, salama, bonjou, saluton, salve, and this sentence keeps all these words together so you can test word-level and sentence-level multilingual detection inside one paragraph.
La tecnología ha cambiado la manera en que las personas viven, trabajan y se comunican. Hoy en día, muchas tareas que antes tomaban horas pueden completarse en pocos minutos gracias a las herramientas digitales. Además, el acceso a la información es más rápido que nunca, lo que permite a los estudiantes y profesionales aprender nuevas habilidades con mayor facilidad. Sin embargo, también es importante usar la tecnología de forma responsable y mantener un equilibrio con la vida personal.
Viajar a un país diferente puede ser una experiencia muy enriquecedora. No solo permite conocer nuevos lugares, sino también descubrir culturas, comidas y tradiciones distintas. Muchas personas consideran que viajar les ayuda a ampliar su perspectiva del mundo y a desarrollar mayor empatía hacia los demás. Aunque a veces puede haber dificultades, como el idioma o la adaptación, los recuerdos y aprendizajes que se obtienen suelen valer mucho la pena.
"""

output = annotate(user_input)
print(output)
