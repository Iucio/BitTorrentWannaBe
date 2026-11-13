#include <bits/stdc++.h>
using namespace std;

inline int add(int a, int b, int p) { return ((a%p) + (b%p)) % p; }
inline int sub(int a, int b, int p) { return (((a%p) - (b%p)) % p + p) % p; }
inline int mult(int a, int b, int p) { return ((long long)(a%p) * (b%p)) % p; }
int binpow(int a, int b, int p) {
    int ans = 1;
    while (b) {
        if (b & 1) ans = mult(ans, a, p);
        a = mult(a, a, p);
        b >>= 1;
    }
    return ans;
}
inline int inv(int a, int p) { return binpow(a, p-2, p); }


int eval(vector<int> a, int x, int p) {
    int ans = 0;
    int xx = 1;
    for (int aa : a) {
        ans = add(ans, mult(aa, xx, p), p);
        xx = mult(xx, x, p);
    }
    return ans;
}

set<pair<int, int>> gen_keys(int S, int n, int k, int p) {
    random_device mt;
    uniform_int_distribution<int> coef(0, p - 1);
    uniform_int_distribution<int> nao_zero(1, p - 1); 

    vector<int> a(k);
    a[0] = S;
    for (int i=1; i<k; i++) a[i] = coef(mt);
    if (k > 1) a[k-1] = nao_zero(mt);

    set<pair<int, int>> keys;
    while (keys.size() < n) {
        int x = nao_zero(mt);
        int y = eval(a, x, p);
        keys.insert(make_pair(x, y));
    }

    return keys;
}

int interpol(set<pair<int, int>> points, int x, int p) {
    int k = points.size();
    
    vector<pair<int, int>> ps;
    for (pair<int, int> point : points) ps.push_back(point);

    vector<int> l(k, 1);
    for (int j=0; j<k; j++) {
        for (int i=0; i<k; i++) if (i != j) {
            int n = sub(x, ps[i].first, p);
            int m = sub(ps[j].first, ps[i].first, p);
            l[j] = mult(l[j], mult(n, inv(m, p), p), p);
        }
    }

    int L = 0;
    for (int j=0; j<k; j++) {
        L = add(L, mult(ps[j].second, l[j], p), p);
    }

    return L;
}


int main() {
    int p = int(1e9) + 7;

    int op = 1;
    do {
        cout << "Escolha:\n";
        cout << "0: Sair\n";
        cout << "1: Gerar chaves\n";
        cout << "2: Revelar o segredo\n";
        cout << "3: Criar mais chaves\n";
        cin >> op;
    
        if (op == 1) {
            int S, n, k = INT32_MAX;
            cout << "Segredo: "; cin >> S;
            cout << "n: "; cin >> n;
            do {
                cout << "k: "; cin >> k;
            } while (k > n);
            
            set<pair<int, int>> keys = gen_keys(S, n, k, p);
            for (pair<int, int> key : keys) {
                cout << '(' << key.first << ", " << key.second << ')' << '\n';
            }
        } else if (op == 2) {
            int k;
            cout << "k: "; cin >> k;

            set<pair<int, int>> keys;
            while (keys.size() < k) {
                int x, y;
                cout << "x: "; cin >> x;
                cout << "y: "; cin >> y;
                keys.insert(make_pair(x, y));
            }

            cout << interpol(keys, 0, p) << '\n';
        } else if (op == 3) {
            int k; cout << "k: "; cin >> k;
            int n; cout << "n: "; cin >> n;

            set<pair<int, int>> keys;
            while (keys.size() < k) {
                int x, y;
                cout << "x: "; cin >> x;
                cout << "y: "; cin >> y;
                keys.insert(make_pair(x, y));
            }

            random_device mt;
            uniform_int_distribution<int> dist(1, p - 1);

            for (int i=0; i<n; i++) {
                int x = dist(mt);
                int y = interpol(keys, x, p);
                cout << "(" << x << ", " << y << ")\n";
            }
        }
    } while (op);
}
