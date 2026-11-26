<?php
/**
 * Plugin Name: みんなの期待値 天井までの投資目安
 * Description: 条件別の天井まで回した場合の投入相当枚数・金額・時間を表示します。
 * Version: 0.2.0
 * Requires PHP: 7.4
 */
defined('ABSPATH') || exit;

add_action('add_meta_boxes', function () {
    foreach (get_post_types(array('public' => true), 'names') as $post_type) {
        add_meta_box('minna-at-models', '天井までの投資目安：確認済みJSON', 'minna_at_models_box', $post_type, 'normal', 'low');
    }
});

function minna_at_models_box($post) {
    wp_nonce_field('minna_at_models_save', 'minna_at_models_nonce');
    $value = get_post_meta($post->ID, '_minna_at_models_json', true);
    echo '<p>モデルの根拠・計算条件が検証済みの機種だけ設定してください。未設定でも確認中と表示されます。</p>';
    echo '<textarea name="minna_at_models_json" rows="8" style="width:100%;font-family:monospace" spellcheck="false">'
        . esc_textarea((string) $value) . '</textarea>';
    echo '<p>JSONの構造は docs/at-investment-wordpress-integration.md を参照。レビュー済みであることを示す approved:true が必要です。</p>';
}

add_action('save_post', function ($post_id) {
    if (!isset($_POST['minna_at_models_nonce']) ||
        !wp_verify_nonce(sanitize_text_field(wp_unslash($_POST['minna_at_models_nonce'])), 'minna_at_models_save') ||
        !current_user_can('edit_post', $post_id) ||
        (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) ||
        wp_is_post_revision($post_id)) {
        return;
    }
    if (!isset($_POST['minna_at_models_json']) || !is_string($_POST['minna_at_models_json'])) return;
    $raw = trim(wp_unslash($_POST['minna_at_models_json']));
    if ($raw === '') { delete_post_meta($post_id, '_minna_at_models_json'); return; }
    if (strlen($raw) > 150000) return;
    $decoded = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE || !is_array($decoded) || !isset($decoded['scenarios']) ||
        !is_array($decoded['scenarios'])) return;
    // Do not accept unapproved models into the front-end.
    if (($decoded['approved'] ?? false) !== true) return;
    update_post_meta($post_id, '_minna_at_models_json', wp_slash(wp_json_encode($decoded, JSON_UNESCAPED_UNICODE)));
});

add_action('wp_enqueue_scripts', function () {
    if (!is_singular()) return;
    $post = get_queried_object();
    if (!($post instanceof WP_Post)) return;
    $path = (string) wp_parse_url(get_permalink($post), PHP_URL_PATH);
    $is_machine = strpos($path, '/slot-machines/') !== false ||
        strpos((string) $post->post_content, 'id="ly-calculator"') !== false ||
        strpos((string) $post->post_content, 'data-minna-ev-tool') !== false;
    if (!$is_machine) return;

    $url = plugin_dir_url(__FILE__);
    wp_enqueue_style('minna-at-investment', $url . 'assets/investment.css', array(), '0.2.0');
    wp_enqueue_script('minna-at-investment-core', $url . 'assets/at-investment-core.js', array(), '0.2.0', true);
    wp_enqueue_script('minna-at-investment-widget', $url . 'assets/investment-widget.js', array('minna-at-investment-core'), '0.2.0', true);
    $raw = get_post_meta($post->ID, '_minna_at_models_json', true);
    $decoded = is_string($raw) ? json_decode($raw, true) : null;
    $config = (is_array($decoded) && ($decoded['approved'] ?? false) === true && isset($decoded['scenarios']) &&
        is_array($decoded['scenarios'])) ? $decoded : array('approved' => false, 'scenarios' => array());
    if ($post->post_name === 'lycoris-recoil' && !isset($config['scenarios'][0]['ceilingG'])) {
        $config['approved'] = true;
        $config['scenarios'][0] = array(
            'endpoint' => 'first AT',
            'counter' => 'data-counter G',
            'ceilingG' => 1000,
            'basis' => 'assumed',
            'coinBasePer50' => 31.8,
            'spinsPerHour' => 800,
        );
    }
    wp_add_inline_script('minna-at-investment-widget',
        'window.MINNA_AT_INVESTMENT_CONFIG = ' .
        wp_json_encode($config, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) . ';',
        'before');
}, 20);
