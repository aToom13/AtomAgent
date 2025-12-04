# 🤖 AtomAgent Prompt Sistemi v2.0

## 📋 Genel Bakış

Bu klasör, AtomAgent'ın tüm agent prompt'larını içerir. Her agent belirli bir uzmanlık alanına sahiptir ve birlikte çalışarak karmaşık görevleri tamamlarlar.

## 🎯 Agent Rolleri

### Temel Agent'lar

| Agent | Dosya | Açıklama |
|-------|-------|----------|
| **Supervisor** | `supervisor_v2.txt` | Master koordinatör - tüm agent'ları yönetir |
| **Coder** | `coder_v2.txt` | Kod geliştirme uzmanı |
| **Researcher** | `researcher_v2.txt` | Araştırma ve bilgi toplama |
| **Planner** | `planner.txt` | Görev planlama ve organizasyon |

### Özel Agent'lar

| Agent | Dosya | Açıklama |
|-------|-------|----------|
| **DevOps** | `devops_agent.txt` | CI/CD, deployment, altyapı |
| **QA** | `qa_agent.txt` | Test ve kalite güvencesi |
| **Security** | `security_agent.txt` | Güvenlik analizi ve denetimi |
| **UI/UX** | `uiux_agent.txt` | Arayüz tasarımı ve kullanıcı deneyimi |
| **Data** | `data_agent.txt` | Veri analizi ve ML |
| **API** | `api_agent.txt` | API tasarımı ve entegrasyon |

## 🔧 Prompt Yapısı

Her prompt şu bölümleri içerir:

```markdown
# AGENT ADI - ROL v1.0

## 🎯 KİMLİK VE MİSYON
[Agent'ın kim olduğu ve temel görevi]

## 🛠️ UZMANLIK ALANLARI
[Teknik yetenekler ve bilgi alanları]

## 📋 OPERASYONEL ÇERÇEVE
[İş akışı ve metodoloji]

## 📝 ŞABLONLAR
[Kod örnekleri ve şablonlar]

## ✅ KONTROL LİSTELERİ
[Kalite kontrol maddeleri]

## 🎯 ÇIKTI FORMATI
[Beklenen çıktı yapısı]
```

## 📊 Agent Seçim Rehberi

### Görev Türüne Göre Agent Seçimi

| Görev Türü | Birincil Agent | Destekleyici Agent'lar |
|------------|----------------|------------------------|
| Yeni özellik geliştirme | Coder | Researcher, QA |
| Bug düzeltme | Coder | QA, Security |
| Performans optimizasyonu | Coder | DevOps, Data |
| Güvenlik denetimi | Security | Coder, DevOps |
| UI geliştirme | UI/UX | Coder |
| API tasarımı | API | Coder, Security |
| Veri analizi | Data | Researcher |
| Deployment | DevOps | QA, Security |
| Araştırma | Researcher | - |
| Proje planlama | Supervisor | Planner |

## 🔄 Agent İletişim Protokolü

### Supervisor → Diğer Agent'lar

```
1. Görev tanımı ve bağlam
2. Başarı kriterleri
3. Zaman kısıtları
4. Bağımlılıklar
```

### Agent → Supervisor

```
1. Durum güncellemesi
2. Tamamlanan işler
3. Karşılaşılan sorunlar
4. Sonraki adımlar
```

## 📈 Versiyon Geçmişi

| Versiyon | Tarih | Değişiklikler |
|----------|-------|---------------|
| v2.0 | 2024-12 | Yeni agent'lar eklendi (DevOps, QA, Security, UI/UX, Data, API) |
| v1.0 | 2024-11 | İlk sürüm (Supervisor, Coder, Researcher, Planner) |

## 🔗 İlgili Dosyalar

- `tools/new_tools_spec.json` - Yeni tool tanımları
- `analysis_report.md` - Agent analiz raporu

## 📝 Notlar

### Best Practices

1. **Prompt Güncellemeleri**: Prompt'ları güncellerken versiyon numarasını artır
2. **Test**: Yeni prompt'ları test ortamında dene
3. **Dokümantasyon**: Değişiklikleri bu README'de belgele
4. **Tutarlılık**: Tüm prompt'larda aynı format yapısını kullan

### Dikkat Edilecekler

- Agent'lar arası çakışmalardan kaçın
- Her agent'ın sorumluluk alanını net tut
- Gereksiz karmaşıklıktan kaçın
- Kullanıcı geri bildirimlerini değerlendir

## 🤝 Katkıda Bulunma

Yeni agent önerileri veya mevcut prompt iyileştirmeleri için:

1. Analiz raporu oluştur
2. Prompt taslağı hazırla
3. Test et
4. Dokümante et
