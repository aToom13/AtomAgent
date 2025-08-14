# PRD — CrewAI Tabanlı Çok Ajanlı Geliştirme Ortamı

## 1. Proje Adı
**AtomAgent**

## 2. Proje Tanımı
Bu proje, kullanıcıların doğal dil ile yazılım geliştirme süreçlerini başlatabileceği, yönlendirebileceği ve takip edebileceği **çok ajanlı bir geliştirme ortamı**dır.  

Sistem, **CrewAI** altyapısını kullanarak farklı uzmanlık alanlarına sahip yapay zekâ ajanlarını bir araya getirir.  

Her ajan, farklı büyük dil modelleri (LLM) ile desteklenebilir(OpenRooter apı kullanılır).

Her ajanın kendine ait bir sandbox ortamı(Kendi dosya dizini ve kendine ait terminali(Birinin terminali diğerini etkilememeli, Birinde kurulan program diğerinde kurulmamalı))

Ajanların ortak kullanım ve dosya paylaşımı yapabilecekleri bir sistem.

Kullanıcı arayüzü **Manus AI benzeri**, modern, karanlık temalı ve token-token gerçek zamanlı sohbet akışı sunar.

## 3. Hedefler
- Kullanıcıya tek bir noktadan **fikirden üretime** yazılım geliştirme imkânı sunmak.
- İstekleri, zorluk seviyesine göre **otomatik sınıflandırmak**.
- Basit soruları doğrudan yanıtlamak, gelişmiş istekleri **multi-agent iş akışı** ile çözmek.
- Farklı ajanlara farklı LLM modelleri atayabilmek.
- Ajanların kendilerine ait sandbox ortamlarının olması
- Arayüz üzerinden ajan ayarlarını kolayca değiştirebilmek.
- Arayüzde ajanların sandbox çalışmalarını canlı olarak görebileceğimiz bir artifact paneli(Kod yazmaları, dosya işlemleri, web gezinmeleri)
- Proje sürecini ve ajanlar arası iletişimi **gerçek zamanlı** izleyebilmek.

## 4. Kullanıcı Akışı

### 4.1. Basit Prompt Senaryosu
1. Kullanıcı bir prompt girer (ör: “Merhaba”).
2. Sohbet Ajanı (Chat Agent) promptu analiz eder.
3. Basit sınıfına giren promptlar doğrudan Sohbet Ajanı tarafından yanıtlanır.
4. Kullanıcı cevabı anında alır.

### 4.2. Gelişmiş Prompt Senaryosu
1. Kullanıcı karmaşık bir proje talebi girer (örn: “Python backend ile Amazon’a benzeyen bir web sitesi istiyorum”).
2. Sohbet Ajanı promptu **“Gelişmiş”** olarak sınıflandırır.
3. Sohbet Ajanı, kullanıcıya bilgilendirme yapar ve talebi **Task Manager** ajanına iletir.
4. Task Manager gerekli ajanları belirler:
   - **Coder**
   - **DB Manager**
   - **Browser Agent**
   - **File Reader**
   - **Tester**
   - **Coordinator**
5. Task Manager ajanları görevlendirir ve görev dağılımını kullanıcıya raporlar.
6. Ajanlar arasında aşağıdaki döngü başlar:
   - Coder kod yazar, DB Manager veritabanı yapılandırır, Browser Agent araştırma yapar, File Reader dosya okur.
   - Tester kodları yükleyip adım adım test eder, sorunları tespit edip raporlar.
   - Coordinator, Tester’ın onayı sonrası proje dosyalarını düzenler ve README.md oluşturur.
   - Task Manager, projeyi çalıştırmayı dener ve adıma adım yaptığı işlemler ve aldığı sonuçları not alır. Proje çalışmazsa aldığı hataları coordinatöre iletir ve coordinator bir görev dağalımı oluşturur diğer agentlar düzeltmeleri yaparlar proje çalışana kadar bu döngü devam eder.
   - Başarısızlık durumunda hata döngüsü tekrar çalışır.
7. Proje başarıyla tamamlandığında proje coordinator tarafından Task Manager kullanıcıya **çalışır ve adım adım detaylı kurulum ve hata klavuzu hazırlanmış(Tester ın kurulum ve test yaparken aldığı zonuçlardan oluşturulur) durumda** teslim eder.

## 5. Teknik Gereksinimler

### 5.1. Altyapı
- **CrewAI** framework
- **OpenRouter API** üzerinden model erişimi
- Her ajan için ayrı model seçebilme desteği
- Token bazlı gerçek zamanlı yanıt akışı (streaming)

### 5.2. Ajanlar ve Model Atamaları
| Ajan        | Örnek Model      |
|-------------|-----------------|
| Chat Agent  | LLaMA           |
| TaskManager | GLM-4.5         |
| Coder       | QwenCoder       |
| DB Manager  | Kimi-K2         |
| File Reader | Deepseek-R1     |
| Tester      | GLM-4.5         |
| Coordinator | Kimi-K2         |

### 5.3. Arayüz Gereksinimleri
- Manus AI benzeri **modern, karanlık tema**
- Token-token gerçek zamanlı akış
- Her ajan konuşmasının ayrı renk ve ikon ile gösterilmesi
- Model ayar ekranı (Ajan > Model eşleştirmesi)
- Proje durumu, görev listesi ve hata takibi paneli
- Çıktı dosyalarının önizleme ve indirme desteği

## 6. İş Akışı Diyagramı (Özet)
Kullanıcı Promptu → Chat Agent →
Basit? → Evet → Direkt Yanıt
Hayır → Task Manager → Agent Görevlendirme → Çalışma Döngüsü → Tester Onayı → Coordinator Düzenleme → Task Manager Teslim


## 7. Başarı Kriterleri
- Basit promptların %100 doğru sınıflandırılması
- Gelişmiş projelerde ajanlar arası hatasız iletişim
- Kullanıcıya kesintisiz gerçek zamanlı bilgi akışı
- Arayüzden tüm model atamalarının değiştirilebilir olması
- Projelerin çalışır ve kurulabilir halde teslim edilmesi

## 8. Riskler ve Önlemler
- **Yanlış Prompt Sınıflandırma** → Ek bağlam analizi, threshold optimizasyonu
- **Model Uyumsuzluğu** → API model listesi ve fallback mekanizması
- **Arayüz Gecikmesi** → WebSocket tabanlı streaming ve batching optimizasyonu
- **Kod Çalışmama Sorunları** → Tester ajanında otomatik debug önerileri

## 9. Teslimatlar
- CrewAI altyapılı backend
- Çok ajanlı görev akış sistemi
- Ajanlara sandbox çalışma ortamı
- Ajanlar arası dosya paylaşım sistemi
- Ajanlara ortak dosya havuzu
- OpenRouter API entegrasyonu
- Modern, karanlık temalı web arayüzü
- Model atama paneli
- Proje yönetimi ve hata takibi modülü
